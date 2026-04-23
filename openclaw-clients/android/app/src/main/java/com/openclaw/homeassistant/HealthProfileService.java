package com.openclaw.homeassistant;
import android.util.Log;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/**
 * 健康档案管理服务
 * 支持体重、血压、血糖、运动记录
 */
public class HealthProfileService {

    private static final String TAG = "HealthProfileService";
    private static final String DB_NAME = "health_profile.db";
    private static final int DB_VERSION = 1;

    private DatabaseHelper dbHelper;
    private Context context;

    public HealthProfileService(Context context) {
        this.context = context;
        this.dbHelper = new DatabaseHelper(context);
    }

    /**
     * 数据库帮助类
     */
    private static class DatabaseHelper extends SQLiteOpenHelper {

        public DatabaseHelper(Context context) {
            super(context, DB_NAME, null, DB_VERSION);
        }

        @Override
        public void onCreate(SQLiteDatabase db) {
            // 健康档案表
            db.execSQL("CREATE TABLE IF NOT EXISTS health_profiles (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "member_name TEXT, " +
                    "gender TEXT, " +
                    "birth_date TEXT, " +
                    "height REAL, " +
                    "blood_type TEXT, " +
                    "emergency_contact TEXT, " +
                    "emergency_phone TEXT, " +
                    "created_at TEXT)");

            // 体重记录表
            db.execSQL("CREATE TABLE IF NOT EXISTS weight_records (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "profile_id INTEGER, " +
                    "weight REAL, " +
                    "bmi REAL, " +
                    "note TEXT, " +
                    "recorded_at TEXT)");

            // 血压记录表
            db.execSQL("CREATE TABLE IF NOT EXISTS blood_pressure_records (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "profile_id INTEGER, " +
                    "systolic INTEGER, " +
                    "diastolic INTEGER, " +
                    "pulse INTEGER, " +
                    "note TEXT, " +
                    "recorded_at TEXT)");

            // 血糖记录表
            db.execSQL("CREATE TABLE IF NOT EXISTS blood_glucose_records (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "profile_id INTEGER, " +
                    "glucose REAL, " +
                    "measure_type TEXT, " +
                    "note TEXT, " +
                    "recorded_at TEXT)");

            // 运动记录表
            db.execSQL("CREATE TABLE IF NOT EXISTS exercise_records (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "profile_id INTEGER, " +
                    "exercise_type TEXT, " +
                    "duration_minutes INTEGER, " +
                    "calories INTEGER, " +
                    "distance_km REAL, " +
                    "note TEXT, " +
                    "recorded_at TEXT)");

            // 睡眠记录表
            db.execSQL("CREATE TABLE IF NOT EXISTS sleep_records (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "profile_id INTEGER, " +
                    "sleep_time TEXT, " +
                    "wake_time TEXT, " +
                    "duration_hours REAL, " +
                    "quality TEXT, " +
                    "note TEXT, " +
                    "recorded_at TEXT)");

            // 用药记录表
            db.execSQL("CREATE TABLE IF NOT EXISTS medication_records (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "profile_id INTEGER, " +
                    "medication_name TEXT, " +
                    "dosage TEXT, " +
                    "frequency TEXT, " +
                    "start_date TEXT, " +
                    "end_date TEXT, " +
                    "reminder_time TEXT, " +
                    "note TEXT, " +
                    "is_active INTEGER DEFAULT 1, " +
                    "created_at TEXT)");
        }

        @Override
        public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
            db.execSQL("DROP TABLE IF EXISTS health_profiles");
            db.execSQL("DROP TABLE IF EXISTS weight_records");
            db.execSQL("DROP TABLE IF EXISTS blood_pressure_records");
            db.execSQL("DROP TABLE IF EXISTS blood_glucose_records");
            db.execSQL("DROP TABLE IF EXISTS exercise_records");
            db.execSQL("DROP TABLE IF EXISTS sleep_records");
            db.execSQL("DROP TABLE IF EXISTS medication_records");
            onCreate(db);
        }
    }

    // ========== 健康档案管理 ==========

    /**
     * 创建健康档案
     */
    public long createProfile(String memberName, String gender, String birthDate,
                              double height, String bloodType) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put("member_name", memberName);
        values.put("gender", gender);
        values.put("birth_date", birthDate);
        values.put("height", height);
        values.put("blood_type", bloodType);
        values.put("created_at", System.currentTimeMillis());

        long id = db.insert("health_profiles", null, values);
        db.close();
        return id;
    }

    /**
     * 获取所有健康档案
     */
    public List<JSONObject> getProfiles() {
        List<JSONObject> profiles = new ArrayList<>();
        SQLiteDatabase db = dbHelper.getReadableDatabase();
        Cursor cursor = db.query("health_profiles", null, null, null, null, null, "created_at DESC");

        while (cursor.moveToNext()) {
            JSONObject profile = new JSONObject();
            try {
                profile.put("profile_id", cursor.getLong(cursor.getColumnIndexOrThrow("id")));
                profile.put("member_name", cursor.getString(cursor.getColumnIndexOrThrow("member_name")));
                profile.put("gender", cursor.getString(cursor.getColumnIndexOrThrow("gender")));
                profile.put("birth_date", cursor.getString(cursor.getColumnIndexOrThrow("birth_date")));
                profile.put("height", cursor.getDouble(cursor.getColumnIndexOrThrow("height")));
                profile.put("blood_type", cursor.getString(cursor.getColumnIndexOrThrow("blood_type")));
            } catch (Exception e) {
                Log.e(TAG, "构建健康档案JSON失败", e);
            }
            profiles.add(profile);
        }

        cursor.close();
        db.close();
        return profiles;
    }

    // ========== 体重记录 ==========

    /**
     * 记录体重
     */
    public long recordWeight(long profileId, double weight, String note) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();

        // 计算BMI
        double bmi = 0;
        Cursor profileCursor = db.query("health_profiles", new String[]{"height"},
                "id = ?", new String[]{String.valueOf(profileId)}, null, null, null);
        if (profileCursor.moveToFirst()) {
            double height = profileCursor.getDouble(0);
            if (height > 0) {
                double heightM = height / 100;
                bmi = Math.round(weight / (heightM * heightM) * 10) / 10.0;
            }
        }
        profileCursor.close();

        ContentValues values = new ContentValues();
        values.put("profile_id", profileId);
        values.put("weight", weight);
        values.put("bmi", bmi);
        values.put("note", note);
        values.put("recorded_at", System.currentTimeMillis());

        long id = db.insert("weight_records", null, values);
        db.close();
        return id;
    }

    /**
     * 获取体重历史
     */
    public List<JSONObject> getWeightHistory(long profileId, int days) {
        List<JSONObject> records = new ArrayList<>();
        SQLiteDatabase db = dbHelper.getReadableDatabase();

        long startTime = System.currentTimeMillis() - (days * 24L * 60 * 60 * 1000);
        Cursor cursor = db.query("weight_records", null,
                "profile_id = ? AND recorded_at >= ?",
                new String[]{String.valueOf(profileId), String.valueOf(startTime)},
                null, null, "recorded_at DESC");

        while (cursor.moveToNext()) {
            JSONObject record = new JSONObject();
            try {
                record.put("record_id", cursor.getLong(cursor.getColumnIndexOrThrow("id")));
                record.put("weight", cursor.getDouble(cursor.getColumnIndexOrThrow("weight")));
                record.put("bmi", cursor.getDouble(cursor.getColumnIndexOrThrow("bmi")));
                record.put("note", cursor.getString(cursor.getColumnIndexOrThrow("note")));
                record.put("recorded_at", cursor.getLong(cursor.getColumnIndexOrThrow("recorded_at")));
            } catch (Exception e) {
                Log.e(TAG, "构建记录JSON失败", e);
            }
            records.add(record);
        }

        cursor.close();
        db.close();
        return records;
    }

    // ========== 血压记录 ==========

    /**
     * 记录血压
     */
    public long recordBloodPressure(long profileId, int systolic, int diastolic,
                                     Integer pulse, String note) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put("profile_id", profileId);
        values.put("systolic", systolic);
        values.put("diastolic", diastolic);
        values.put("pulse", pulse != null ? pulse : 0);
        values.put("note", note);
        values.put("recorded_at", System.currentTimeMillis());

        long id = db.insert("blood_pressure_records", null, values);
        db.close();
        return id;
    }

    /**
     * 获取血压历史
     */
    public List<JSONObject> getBloodPressureHistory(long profileId, int days) {
        List<JSONObject> records = new ArrayList<>();
        SQLiteDatabase db = dbHelper.getReadableDatabase();

        long startTime = System.currentTimeMillis() - (days * 24L * 60 * 60 * 1000);
        Cursor cursor = db.query("blood_pressure_records", null,
                "profile_id = ? AND recorded_at >= ?",
                new String[]{String.valueOf(profileId), String.valueOf(startTime)},
                null, null, "recorded_at DESC");

        while (cursor.moveToNext()) {
            JSONObject record = new JSONObject();
            try {
                record.put("record_id", cursor.getLong(cursor.getColumnIndexOrThrow("id")));
                record.put("systolic", cursor.getInt(cursor.getColumnIndexOrThrow("systolic")));
                record.put("diastolic", cursor.getInt(cursor.getColumnIndexOrThrow("diastolic")));
                record.put("pulse", cursor.getInt(cursor.getColumnIndexOrThrow("pulse")));
                record.put("note", cursor.getString(cursor.getColumnIndexOrThrow("note")));
                record.put("recorded_at", cursor.getLong(cursor.getColumnIndexOrThrow("recorded_at")));

                // 评估血压状态
                int sys = cursor.getInt(cursor.getColumnIndexOrThrow("systolic"));
                int dia = cursor.getInt(cursor.getColumnIndexOrThrow("diastolic"));
                record.put("status", evaluateBloodPressure(sys, dia));
            } catch (Exception e) {
                Log.e(TAG, "构建记录JSON失败", e);
            }
            records.add(record);
        }

        cursor.close();
        db.close();
        return records;
    }

    /**
     * 评估血压状态
     */
    private JSONObject evaluateBloodPressure(int systolic, int diastolic) {
        JSONObject status = new JSONObject();
        try {
            if (systolic < 90 || diastolic < 60) {
                status.put("level", "low");
                status.put("message", "血压偏低");
                status.put("color", "blue");
            } else if (systolic < 120 && diastolic < 80) {
                status.put("level", "normal");
                status.put("message", "血压正常");
                status.put("color", "green");
            } else if (systolic < 140 || diastolic < 90) {
                status.put("level", "elevated");
                status.put("message", "血压偏高");
                status.put("color", "yellow");
            } else {
                status.put("level", "high");
                status.put("message", "高血压");
                status.put("color", "red");
            }
        } catch (Exception e) {
            Log.e(TAG, "判断血压状态失败", e);
        }
        return status;
    }

    // ========== 运动记录 ==========

    /**
     * 记录运动
     */
    public long recordExercise(long profileId, String exerciseType, int durationMinutes,
                                Integer calories, Double distanceKm, String note) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();

        // 如果没有提供卡路里，估算
        int estimatedCalories = calories != null ? calories : estimateCalories(exerciseType, durationMinutes);

        ContentValues values = new ContentValues();
        values.put("profile_id", profileId);
        values.put("exercise_type", exerciseType);
        values.put("duration_minutes", durationMinutes);
        values.put("calories", estimatedCalories);
        values.put("distance_km", distanceKm != null ? distanceKm : 0);
        values.put("note", note);
        values.put("recorded_at", System.currentTimeMillis());

        long id = db.insert("exercise_records", null, values);
        db.close();
        return id;
    }

    /**
     * 估算卡路里消耗
     */
    private int estimateCalories(String exerciseType, int durationMinutes) {
        int caloriesPerMin;
        switch (exerciseType.toLowerCase()) {
            case "walking":
                caloriesPerMin = 4;
                break;
            case "running":
                caloriesPerMin = 10;
                break;
            case "swimming":
                caloriesPerMin = 8;
                break;
            case "cycling":
                caloriesPerMin = 7;
                break;
            case "yoga":
                caloriesPerMin = 3;
                break;
            default:
                caloriesPerMin = 5;
        }
        return caloriesPerMin * durationMinutes;
    }

    /**
     * 获取运动历史
     */
    public List<JSONObject> getExerciseHistory(long profileId, int days) {
        List<JSONObject> records = new ArrayList<>();
        SQLiteDatabase db = dbHelper.getReadableDatabase();

        long startTime = System.currentTimeMillis() - (days * 24L * 60 * 60 * 1000);
        Cursor cursor = db.query("exercise_records", null,
                "profile_id = ? AND recorded_at >= ?",
                new String[]{String.valueOf(profileId), String.valueOf(startTime)},
                null, null, "recorded_at DESC");

        while (cursor.moveToNext()) {
            JSONObject record = new JSONObject();
            try {
                record.put("record_id", cursor.getLong(cursor.getColumnIndexOrThrow("id")));
                record.put("exercise_type", cursor.getString(cursor.getColumnIndexOrThrow("exercise_type")));
                record.put("duration_minutes", cursor.getInt(cursor.getColumnIndexOrThrow("duration_minutes")));
                record.put("calories", cursor.getInt(cursor.getColumnIndexOrThrow("calories")));
                record.put("distance_km", cursor.getDouble(cursor.getColumnIndexOrThrow("distance_km")));
                record.put("note", cursor.getString(cursor.getColumnIndexOrThrow("note")));
                record.put("recorded_at", cursor.getLong(cursor.getColumnIndexOrThrow("recorded_at")));
            } catch (Exception e) {
                Log.e(TAG, "构建记录JSON失败", e);
            }
            records.add(record);
        }

        cursor.close();
        db.close();
        return records;
    }

    // ========== 血糖记录 ==========

    /**
     * 记录血糖
     */
    public long recordBloodGlucose(long profileId, double glucose, String measureType, String note) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put("profile_id", profileId);
        values.put("glucose", glucose);
        values.put("measure_type", measureType);
        values.put("note", note);
        values.put("recorded_at", System.currentTimeMillis());

        long id = db.insert("blood_glucose_records", null, values);
        db.close();
        return id;
    }

    // ========== 用药管理 ==========

    /**
     * 添加用药记录
     */
    public long addMedication(long profileId, String medicationName, String dosage,
                               String frequency, String reminderTime, String note) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put("profile_id", profileId);
        values.put("medication_name", medicationName);
        values.put("dosage", dosage);
        values.put("frequency", frequency);
        values.put("reminder_time", reminderTime);
        values.put("note", note);
        values.put("is_active", 1);
        values.put("created_at", System.currentTimeMillis());

        long id = db.insert("medication_records", null, values);
        db.close();
        return id;
    }

    /**
     * 获取用药列表
     */
    public List<JSONObject> getMedications(long profileId) {
        List<JSONObject> medications = new ArrayList<>();
        SQLiteDatabase db = dbHelper.getReadableDatabase();

        Cursor cursor = db.query("medication_records", null,
                "profile_id = ? AND is_active = 1",
                new String[]{String.valueOf(profileId)},
                null, null, "reminder_time");

        while (cursor.moveToNext()) {
            JSONObject med = new JSONObject();
            try {
                med.put("medication_id", cursor.getLong(cursor.getColumnIndexOrThrow("id")));
                med.put("medication_name", cursor.getString(cursor.getColumnIndexOrThrow("medication_name")));
                med.put("dosage", cursor.getString(cursor.getColumnIndexOrThrow("dosage")));
                med.put("frequency", cursor.getString(cursor.getColumnIndexOrThrow("frequency")));
                med.put("reminder_time", cursor.getString(cursor.getColumnIndexOrThrow("reminder_time")));
                med.put("note", cursor.getString(cursor.getColumnIndexOrThrow("note")));
            } catch (Exception e) {
                Log.e(TAG, "构建药物JSON失败", e);
            }
            medications.add(med);
        }

        cursor.close();
        db.close();
        return medications;
    }

    /**
     * 关闭数据库
     */
    public void close() {
        if (dbHelper != null) {
            dbHelper.close();
        }
    }
}