import UIKit
import Flutter

@UIApplicationMain
@objc class AppDelegate: FlutterAppDelegate {
    
    private var backgroundTaskManager: BackgroundTaskManager?
    
    override func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        
        if #available(iOS 13.0, *) {
            backgroundTaskManager = BackgroundTaskManager.shared
            backgroundTaskManager?.registerBackgroundTasks()
        }
        
        let controller = window?.rootViewController as? FlutterViewController
        let healthChannel = FlutterMethodChannel(
            name: "com.openclaw.health",
            binaryMessenger: controller!.binaryMessenger
        )
        
        healthChannel.setMethodCallHandler { [weak self] (call, result) in
            switch call.method {
            case "initialize":
                result(nil)
                
            case "enableBackgroundUpdates":
                self?.backgroundTaskManager?.enableBackgroundUpdates { success in
                    DispatchQueue.main.async {
                        result(success)
                    }
                }
                
            case "disableBackgroundUpdates":
                self?.backgroundTaskManager?.disableBackgroundUpdates()
                result(nil)
                
            default:
                result(FlutterMethodNotImplemented)
            }
        }
        
        GeneratedPluginRegistrant.register(with: self)
        return super.application(application, didFinishLaunchingOptions: launchOptions)
    }
    
    func application(_ application: UIApplication, handleEventsForBackgroundURLSession identifier: String, completionHandler: @escaping () -> Void) {
        completionHandler()
    }
}