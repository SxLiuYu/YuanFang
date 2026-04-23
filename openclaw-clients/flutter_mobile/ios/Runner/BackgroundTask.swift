import UIKit
import BackgroundTasks
import HealthKit
import CoreLocation

@available(iOS 13.0, *)
class BackgroundTaskManager: NSObject {
    
    static let shared = BackgroundTaskManager()
    
    private let healthStore = HKHealthStore()
    private let locationManager = CLLocationManager()
    
    private var backgroundSyncTaskIdentifier = "com.openclaw.health.sync"
    private var backgroundLocationTaskIdentifier = "com.openclaw.location.update"
    
    private var pendingCompletionHandlers: [String: () -> Void] = [:]
    
    private override init() {
        super.init()
    }
    
    // MARK: - Registration
    
    func registerBackgroundTasks() {
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: backgroundSyncTaskIdentifier,
            using: nil
        ) { task in
            self.handleHealthSyncTask(task: task as! BGAppRefreshTask)
        }
        
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: backgroundLocationTaskIdentifier,
            using: nil
        ) { task in
            self.handleLocationUpdateTask(task: task as! BGAppRefreshTask)
        }
        
        NSLog("[BackgroundTask] Registered background tasks")
    }
    
    func scheduleHealthSyncTask() {
        let request = BGAppRefreshTaskRequest(identifier: backgroundSyncTaskIdentifier)
        request.earliestBeginDate = Date(time: Date().timeIntervalSinceNow + 3600)
        
        do {
            try BGTaskScheduler.shared.submit(request)
            NSLog("[BackgroundTask] Scheduled health sync task")
        } catch {
            NSLog("[BackgroundTask] Failed to schedule health sync: \(error)")
        }
    }
    
    func scheduleLocationUpdateTask() {
        let request = BGAppRefreshTaskRequest(identifier: backgroundLocationTaskIdentifier)
        request.earliestBeginDate = Date(time: Date().timeIntervalSinceNow + 1800)
        
        do {
            try BGTaskScheduler.shared.submit(request)
            NSLog("[BackgroundTask] Scheduled location update task")
        } catch {
            NSLog("[BackgroundTask] Failed to schedule location update: \(error)")
        }
    }
    
    // MARK: - Health Sync Task
    
    private func handleHealthSyncTask(task: BGAppRefreshTask) {
        task.expirationHandler = {
            NSLog("[BackgroundTask] Health sync task expired")
            task.setTaskCompleted(success: false)
        }
        
        NSLog("[BackgroundTask] Starting health sync task")
        
        syncHealthData { success in
            self.scheduleHealthSyncTask()
            task.setTaskCompleted(success: success)
        }
    }
    
    private func syncHealthData(completion: @escaping (Bool) -> Void) {
        guard HKHealthStore.isHealthDataAvailable() else {
            NSLog("[BackgroundTask] HealthKit not available")
            completion(false)
            return
        }
        
        let dispatchGroup = DispatchGroup()
        var syncSuccess = true
        
        let typesToRead: [HKSampleType] = [
            HKObjectType.quantityType(forIdentifier: .stepCount)!,
            HKObjectType.quantityType(forIdentifier: .heartRate)!,
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!,
            HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!
        ]
        
        dispatchGroup.enter()
        healthStore.requestAuthorization(toShare: nil, read: Set(typesToRead)) { success, error in
            if !success {
                NSLog("[BackgroundTask] Health authorization denied: \(String(describing: error))")
                syncSuccess = false
            }
            dispatchGroup.leave()
        }
        
        dispatchGroup.notify(queue: .global()) {
            guard syncSuccess else {
                completion(false)
                return
            }
            
            self.fetchAndSyncHealthData { success in
                completion(success)
            }
        }
    }
    
    private func fetchAndSyncHealthData(completion: @escaping (Bool) -> Void) {
        let now = Date()
        let startOfDay = Calendar.current.startOfDay(for: now)
        
        var healthData: [String: Any] = [
            "timestamp": ISO8601DateFormatter().string(from: now)
        ]
        
        let dispatchGroup = DispatchGroup()
        
        dispatchGroup.enter()
        fetchStepCount(start: startOfDay, end: now) { steps in
            if let steps = steps {
                healthData["steps"] = steps
            }
            dispatchGroup.leave()
        }
        
        dispatchGroup.enter()
        fetchHeartRate(start: now.addingTimeInterval(-3600), end: now) { heartRate in
            if let heartRate = heartRate {
                healthData["heart_rate"] = heartRate
            }
            dispatchGroup.leave()
        }
        
        dispatchGroup.enter()
        fetchActiveEnergy(start: startOfDay, end: now) { calories in
            if let calories = calories {
                healthData["calories"] = calories
            }
            dispatchGroup.leave()
        }
        
        dispatchGroup.notify(queue: .global()) {
            self.sendHealthDataToServer(healthData) { success in
                NSLog("[BackgroundTask] Health data sync completed: \(success)")
                completion(success)
            }
        }
    }
    
    private func fetchStepCount(start: Date, end: Date, completion: @escaping (Int?) -> Void) {
        guard let stepType = HKObjectType.quantityType(forIdentifier: .stepCount) else {
            completion(nil)
            return
        }
        
        let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: .strictStartDate)
        let query = HKStatisticsQuery(quantityType: stepType, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, result, error in
            guard let result = result, let sum = result.sumQuantity() else {
                NSLog("[BackgroundTask] Step count query error: \(String(describing: error))")
                completion(nil)
                return
            }
            completion(Int(sum.doubleValue(for: HKUnit.count())))
        }
        
        healthStore.execute(query)
    }
    
    private func fetchHeartRate(start: Date, end: Date, completion: @escaping (Int?) -> Void) {
        guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else {
            completion(nil)
            return
        }
        
        let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: .strictStartDate)
        let sortDescriptor = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: false)
        let query = HKSampleQuery(sampleType: heartRateType, predicate: predicate, limit: 1, sortDescriptors: [sortDescriptor]) { _, samples, error in
            guard let sample = samples?.first as? HKQuantitySample else {
                NSLog("[BackgroundTask] Heart rate query error: \(String(describing: error))")
                completion(nil)
                return
            }
            let heartRateUnit = HKUnit.count().unitDivided(by: .minute())
            completion(Int(sample.quantity.doubleValue(for: heartRateUnit)))
        }
        
        healthStore.execute(query)
    }
    
    private func fetchActiveEnergy(start: Date, end: Date, completion: @escaping (Int?) -> Void) {
        guard let energyType = HKObjectType.quantityType(forIdentifier: .activeEnergyBurned) else {
            completion(nil)
            return
        }
        
        let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: .strictStartDate)
        let query = HKStatisticsQuery(quantityType: energyType, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, result, error in
            guard let result = result, let sum = result.sumQuantity() else {
                NSLog("[BackgroundTask] Active energy query error: \(String(describing: error))")
                completion(nil)
                return
            }
            completion(Int(sum.doubleValue(for: HKUnit.kilocalorie())))
        }
        
        healthStore.execute(query)
    }
    
    private func sendHealthDataToServer(_ data: [String: Any], completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "http://localhost:8082/api/v1/health/metrics/record") else {
            completion(false)
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: data)
        } catch {
            NSLog("[BackgroundTask] JSON serialization error: \(error)")
            completion(false)
            return
        }
        
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                NSLog("[BackgroundTask] Server request error: \(error)")
                completion(false)
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                NSLog("[BackgroundTask] Server returned error")
                completion(false)
                return
            }
            
            NSLog("[BackgroundTask] Health data sent successfully")
            completion(true)
        }
        
        task.resume()
    }
    
    // MARK: - Location Update Task
    
    private func handleLocationUpdateTask(task: BGAppRefreshTask) {
        task.expirationHandler = {
            NSLog("[BackgroundTask] Location update task expired")
            task.setTaskCompleted(success: false)
        }
        
        NSLog("[BackgroundTask] Starting location update task")
        
        locationManager.requestWhenInUseAuthorization()
        locationManager.desiredAccuracy = kCLLocationAccuracyHundredMeters
        locationManager.distanceFilter = 100
        
        if #available(iOS 14.0, *) {
            locationManager.authorizationMode = .accurate
        }
        
        locationManager.startUpdatingLocation()
        
        DispatchQueue.global().asyncAfter(deadline: .now() + 30) { [weak self] in
            self?.locationManager.stopUpdatingLocation()
            self?.scheduleLocationUpdateTask()
            task.setTaskCompleted(success: true)
        }
    }
    
    // MARK: - Flutter Method Channel Support
    
    func enableBackgroundUpdates(completion: @escaping (Bool) -> Void) {
        requestHealthAuthorization { success in
            if success {
                self.scheduleHealthSyncTask()
                self.scheduleLocationUpdateTask()
                NSLog("[BackgroundTask] Background updates enabled")
            }
            completion(success)
        }
    }
    
    func disableBackgroundUpdates() {
        BGTaskScheduler.shared.cancel(taskRequestWithIdentifier: backgroundSyncTaskIdentifier)
        BGTaskScheduler.shared.cancel(taskRequestWithIdentifier: backgroundLocationTaskIdentifier)
        NSLog("[BackgroundTask] Background updates disabled")
    }
    
    private func requestHealthAuthorization(completion: @escaping (Bool) -> Void) {
        guard HKHealthStore.isHealthDataAvailable() else {
            completion(false)
            return
        }
        
        let typesToRead: Set<HKObjectType> = [
            HKObjectType.quantityType(forIdentifier: .stepCount)!,
            HKObjectType.quantityType(forIdentifier: .heartRate)!,
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!,
            HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!
        ]
        
        healthStore.requestAuthorization(toShare: nil, read: typesToRead) { success, error in
            if let error = error {
                NSLog("[BackgroundTask] Authorization error: \(error)")
            }
            completion(success)
        }
    }
}

// MARK: - AppDelegate Integration

@available(iOS 13.0, *)
extension AppDelegate {
    
    func setupBackgroundTasks() {
        BackgroundTaskManager.shared.registerBackgroundTasks()
    }
}