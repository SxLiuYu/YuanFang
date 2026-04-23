import logging
logger = logging.getLogger(__name__)
"""
健康档案管理服务
支持体重、血压、血糖、运动记录、健康报告生成
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class HealthProfileService:
    """健康档案管理服务"""

    def __init__(self, db_path: str = 'family_services.db'):
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """初始化健康档案相关表"""
        conn = self._get_conn()
        c = conn.cursor()

        # 健康档案主表
        c.execute('''
            CREATE TABLE IF NOT EXISTS health_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                member_name TEXT,
                gender TEXT,
                birth_date DATE,
                height REAL,
                blood_type TEXT,
                emergency_contact TEXT,
                emergency_phone TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')

        # 体重记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS weight_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER,
                weight REAL,
                bmi REAL,
                note TEXT,
                recorded_at TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES health_profiles(id)
            )
        ''')

        # 血压记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS blood_pressure_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER,
                systolic INTEGER,
                diastolic INTEGER,
                pulse INTEGER,
                note TEXT,
                recorded_at TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES health_profiles(id)
            )
        ''')

        # 血糖记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS blood_glucose_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER,
                glucose REAL,
                measure_type TEXT,
                note TEXT,
                recorded_at TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES health_profiles(id)
            )
        ''')

        # 运动记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS exercise_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER,
                exercise_type TEXT,
                duration_minutes INTEGER,
                calories INTEGER,
                distance_km REAL,
                note TEXT,
                recorded_at TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES health_profiles(id)
            )
        ''')

        # 睡眠记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS sleep_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER,
                sleep_time TIME,
                wake_time TIME,
                duration_hours REAL,
                quality TEXT,
                note TEXT,
                recorded_at TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES health_profiles(id)
            )
        ''')

        # 用药记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS medication_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER,
                medication_name TEXT,
                dosage TEXT,
                frequency TEXT,
                start_date DATE,
                end_date DATE,
                reminder_time TIME,
                note TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP
            )
        ''')

        # 健康提醒表
        c.execute('''
            CREATE TABLE IF NOT EXISTS health_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER,
                reminder_type TEXT,
                reminder_title TEXT,
                reminder_content TEXT,
                reminder_time TIME,
                is_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    # ========== 健康档案管理 ==========

    def create_profile(self, member_name: str, gender: str = 'unknown',
                       birth_date: str = None, height: float = 0,
                       blood_type: str = None, emergency_contact: str = None,
                       emergency_phone: str = None) -> Dict[str, Any]:
        """创建健康档案"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            c.execute('''
                INSERT INTO health_profiles
                (member_name, gender, birth_date, height, blood_type,
                 emergency_contact, emergency_phone, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (member_name, gender, birth_date, height, blood_type,
                  emergency_contact, emergency_phone, datetime.now(), datetime.now()))

            profile_id = c.lastrowid
            conn.commit()

            return {'success': True, 'profile_id': profile_id}

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_profiles(self) -> List[Dict[str, Any]]:
        """获取所有健康档案"""
        conn = self._get_conn()
        c = conn.cursor()

        c.execute('SELECT * FROM health_profiles ORDER BY created_at DESC')

        profiles = []
        for row in c.fetchall():
            profiles.append({
                'profile_id': row['id'],
                'member_name': row['member_name'],
                'gender': row['gender'],
                'birth_date': row['birth_date'],
                'height': row['height'],
                'blood_type': row['blood_type'],
                'emergency_contact': row['emergency_contact'],
                'emergency_phone': row['emergency_phone']
            })

        conn.close()
        return profiles

    def get_profile(self, profile_id: int) -> Optional[Dict[str, Any]]:
        """获取单个健康档案"""
        conn = self._get_conn()
        c = conn.cursor()

        c.execute('SELECT * FROM health_profiles WHERE id = ?', (profile_id,))
        row = c.fetchone()
        conn.close()

        if row:
            return {
                'profile_id': row['id'],
                'member_name': row['member_name'],
                'gender': row['gender'],
                'birth_date': row['birth_date'],
                'height': row['height'],
                'blood_type': row['blood_type'],
                'emergency_contact': row['emergency_contact'],
                'emergency_phone': row['emergency_phone']
            }
        return None

    def update_profile(self, profile_id: int, **kwargs) -> Dict[str, Any]:
        """更新健康档案"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            # 构建更新语句
            updates = []
            values = []
            for key in ['member_name', 'gender', 'birth_date', 'height',
                       'blood_type', 'emergency_contact', 'emergency_phone']:
                if key in kwargs:
                    updates.append(f'{key} = ?')
                    values.append(kwargs[key])

            updates.append('updated_at = ?')
            values.append(datetime.now())
            values.append(profile_id)

            c.execute(f'''
                UPDATE health_profiles
                SET {', '.join(updates)}
                WHERE id = ?
            ''', values)

            conn.commit()
            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    # ========== 体重记录 ==========

    def record_weight(self, profile_id: int, weight: float, note: str = '') -> Dict[str, Any]:
        """记录体重"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            # 计算BMI
            profile = self.get_profile(profile_id)
            bmi = 0
            if profile and profile['height'] > 0:
                height_m = profile['height'] / 100
                bmi = round(weight / (height_m * height_m), 1)

            c.execute('''
                INSERT INTO weight_records
                (profile_id, weight, bmi, note, recorded_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (profile_id, weight, bmi, note, datetime.now()))

            record_id = c.lastrowid
            conn.commit()

            return {'success': True, 'record_id': record_id, 'bmi': bmi}

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_weight_history(self, profile_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """获取体重历史"""
        conn = self._get_conn()
        c = conn.cursor()

        c.execute('''
            SELECT * FROM weight_records
            WHERE profile_id = ? AND recorded_at >= date('now', ?)
            ORDER BY recorded_at DESC
        ''', (profile_id, f'-{days} days'))

        records = []
        for row in c.fetchall():
            records.append({
                'record_id': row['id'],
                'weight': row['weight'],
                'bmi': row['bmi'],
                'note': row['note'],
                'recorded_at': row['recorded_at']
            })

        conn.close()
        return records

    # ========== 血压记录 ==========

    def record_blood_pressure(self, profile_id: int, systolic: int, diastolic: int,
                               pulse: int = None, note: str = '') -> Dict[str, Any]:
        """记录血压"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            c.execute('''
                INSERT INTO blood_pressure_records
                (profile_id, systolic, diastolic, pulse, note, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (profile_id, systolic, diastolic, pulse, note, datetime.now()))

            record_id = c.lastrowid
            conn.commit()

            # 评估血压状态
            status = self._evaluate_blood_pressure(systolic, diastolic)

            return {'success': True, 'record_id': record_id, 'status': status}

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def _evaluate_blood_pressure(self, systolic: int, diastolic: int) -> Dict[str, Any]:
        """评估血压状态"""
        if systolic < 90 or diastolic < 60:
            return {'level': 'low', 'message': '血压偏低', 'color': 'blue'}
        elif systolic < 120 and diastolic < 80:
            return {'level': 'normal', 'message': '血压正常', 'color': 'green'}
        elif systolic < 140 or diastolic < 90:
            return {'level': 'elevated', 'message': '血压偏高', 'color': 'yellow'}
        else:
            return {'level': 'high', 'message': '高血压', 'color': 'red'}

    def get_blood_pressure_history(self, profile_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """获取血压历史"""
        conn = self._get_conn()
        c = conn.cursor()

        c.execute('''
            SELECT * FROM blood_pressure_records
            WHERE profile_id = ? AND recorded_at >= date('now', ?)
            ORDER BY recorded_at DESC
        ''', (profile_id, f'-{days} days'))

        records = []
        for row in c.fetchall():
            status = self._evaluate_blood_pressure(row['systolic'], row['diastolic'])
            records.append({
                'record_id': row['id'],
                'systolic': row['systolic'],
                'diastolic': row['diastolic'],
                'pulse': row['pulse'],
                'note': row['note'],
                'status': status,
                'recorded_at': row['recorded_at']
            })

        conn.close()
        return records

    # ========== 血糖记录 ==========

    def record_blood_glucose(self, profile_id: int, glucose: float,
                              measure_type: str = 'fasting', note: str = '') -> Dict[str, Any]:
        """记录血糖

        measure_type: fasting(空腹), before_meal(餐前), after_meal(餐后), random(随机)
        """
        conn = self._get_conn()
        c = conn.cursor()

        try:
            c.execute('''
                INSERT INTO blood_glucose_records
                (profile_id, glucose, measure_type, note, recorded_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (profile_id, glucose, measure_type, note, datetime.now()))

            record_id = c.lastrowid
            conn.commit()

            # 评估血糖状态
            status = self._evaluate_glucose(glucose, measure_type)

            return {'success': True, 'record_id': record_id, 'status': status}

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def _evaluate_glucose(self, glucose: float, measure_type: str) -> Dict[str, Any]:
        """评估血糖状态"""
        if measure_type == 'fasting':
            if glucose < 3.9:
                return {'level': 'low', 'message': '血糖偏低', 'color': 'blue'}
            elif glucose <= 6.1:
                return {'level': 'normal', 'message': '血糖正常', 'color': 'green'}
            elif glucose <= 7.0:
                return {'level': 'elevated', 'message': '血糖偏高', 'color': 'yellow'}
            else:
                return {'level': 'high', 'message': '血糖过高', 'color': 'red'}
        elif measure_type == 'after_meal':
            if glucose < 3.9:
                return {'level': 'low', 'message': '血糖偏低', 'color': 'blue'}
            elif glucose <= 7.8:
                return {'level': 'normal', 'message': '血糖正常', 'color': 'green'}
            elif glucose <= 11.1:
                return {'level': 'elevated', 'message': '血糖偏高', 'color': 'yellow'}
            else:
                return {'level': 'high', 'message': '血糖过高', 'color': 'red'}
        else:
            return {'level': 'unknown', 'message': '请咨询医生', 'color': 'gray'}

    # ========== 运动记录 ==========

    def record_exercise(self, profile_id: int, exercise_type: str,
                        duration_minutes: int, calories: int = None,
                        distance_km: float = None, note: str = '') -> Dict[str, Any]:
        """记录运动"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            # 如果没有提供卡路里，根据运动类型估算
            if calories is None:
                calories = self._estimate_calories(exercise_type, duration_minutes)

            c.execute('''
                INSERT INTO exercise_records
                (profile_id, exercise_type, duration_minutes, calories, distance_km, note, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (profile_id, exercise_type, duration_minutes, calories, distance_km, note, datetime.now()))

            record_id = c.lastrowid
            conn.commit()

            return {'success': True, 'record_id': record_id, 'calories': calories}

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def _estimate_calories(self, exercise_type: str, duration_minutes: int) -> int:
        """估算卡路里消耗（基于60kg体重）"""
        calories_per_min = {
            'walking': 4,
            'running': 10,
            'swimming': 8,
            'cycling': 7,
            'yoga': 3,
            'basketball': 8,
            'football': 9,
            'badminton': 6,
            'tennis': 7,
            'gym': 5
        }
        return int(calories_per_min.get(exercise_type, 5) * duration_minutes)

    def get_exercise_history(self, profile_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """获取运动历史"""
        conn = self._get_conn()
        c = conn.cursor()

        c.execute('''
            SELECT * FROM exercise_records
            WHERE profile_id = ? AND recorded_at >= date('now', ?)
            ORDER BY recorded_at DESC
        ''', (profile_id, f'-{days} days'))

        records = []
        for row in c.fetchall():
            records.append({
                'record_id': row['id'],
                'exercise_type': row['exercise_type'],
                'duration_minutes': row['duration_minutes'],
                'calories': row['calories'],
                'distance_km': row['distance_km'],
                'note': row['note'],
                'recorded_at': row['recorded_at']
            })

        conn.close()
        return records

    # ========== 睡眠记录 ==========

    def record_sleep(self, profile_id: int, sleep_time: str, wake_time: str,
                     quality: str = 'normal', note: str = '') -> Dict[str, Any]:
        """记录睡眠"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            # 计算睡眠时长
            from datetime import datetime as dt
            sleep_dt = dt.strptime(sleep_time, '%H:%M')
            wake_dt = dt.strptime(wake_time, '%H:%M')

            if wake_dt < sleep_dt:
                wake_dt += timedelta(days=1)

            duration_hours = round((wake_dt - sleep_dt).seconds / 3600, 1)

            c.execute('''
                INSERT INTO sleep_records
                (profile_id, sleep_time, wake_time, duration_hours, quality, note, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (profile_id, sleep_time, wake_time, duration_hours, quality, note, datetime.now()))

            record_id = c.lastrowid
            conn.commit()

            return {'success': True, 'record_id': record_id, 'duration_hours': duration_hours}

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_sleep_history(self, profile_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """获取睡眠历史"""
        conn = self._get_conn()
        c = conn.cursor()

        c.execute('''
            SELECT * FROM sleep_records
            WHERE profile_id = ? AND recorded_at >= date('now', ?)
            ORDER BY recorded_at DESC
        ''', (profile_id, f'-{days} days'))

        records = []
        for row in c.fetchall():
            records.append({
                'record_id': row['id'],
                'sleep_time': row['sleep_time'],
                'wake_time': row['wake_time'],
                'duration_hours': row['duration_hours'],
                'quality': row['quality'],
                'note': row['note'],
                'recorded_at': row['recorded_at']
            })

        conn.close()
        return records

    # ========== 用药管理 ==========

    def add_medication(self, profile_id: int, medication_name: str,
                       dosage: str, frequency: str, start_date: str = None,
                       end_date: str = None, reminder_time: str = None,
                       note: str = '') -> Dict[str, Any]:
        """添加用药记录"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            c.execute('''
                INSERT INTO medication_records
                (profile_id, medication_name, dosage, frequency, start_date, end_date,
                 reminder_time, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (profile_id, medication_name, dosage, frequency, start_date, end_date,
                  reminder_time, note, datetime.now()))

            record_id = c.lastrowid
            conn.commit()

            return {'success': True, 'medication_id': record_id}

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_medications(self, profile_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """获取用药列表"""
        conn = self._get_conn()
        c = conn.cursor()

        if active_only:
            c.execute('''
                SELECT * FROM medication_records
                WHERE profile_id = ? AND is_active = 1
                ORDER BY reminder_time
            ''', (profile_id,))
        else:
            c.execute('''
                SELECT * FROM medication_records
                WHERE profile_id = ?
                ORDER BY created_at DESC
            ''', (profile_id,))

        medications = []
        for row in c.fetchall():
            medications.append({
                'medication_id': row['id'],
                'medication_name': row['medication_name'],
                'dosage': row['dosage'],
                'frequency': row['frequency'],
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'reminder_time': row['reminder_time'],
                'note': row['note'],
                'is_active': row['is_active']
            })

        conn.close()
        return medications

    # ========== 健康报告 ==========

    def generate_health_report(self, profile_id: int, days: int = 30) -> Dict[str, Any]:
        """生成健康报告"""
        profile = self.get_profile(profile_id)
        if not profile:
            return {'success': False, 'error': '档案不存在'}

        # 获取各项数据
        weight_history = self.get_weight_history(profile_id, days)
        bp_history = self.get_blood_pressure_history(profile_id, days)
        exercise_history = self.get_exercise_history(profile_id, days)
        sleep_history = self.get_sleep_history(profile_id, days)

        # 计算统计数据
        report = {
            'success': True,
            'profile': profile,
            'period': f'最近{days}天',
            'generated_at': datetime.now().isoformat(),
            'weight': self._analyze_weight(weight_history),
            'blood_pressure': self._analyze_blood_pressure(bp_history),
            'exercise': self._analyze_exercise(exercise_history),
            'sleep': self._analyze_sleep(sleep_history),
            'recommendations': []
        }

        # 生成建议
        report['recommendations'] = self._generate_recommendations(report)

        return report

    def _analyze_weight(self, history: List[Dict]) -> Dict[str, Any]:
        """分析体重数据"""
        if not history:
            return {'has_data': False}

        weights = [h['weight'] for h in history]
        latest = history[0]

        return {
            'has_data': True,
            'latest_weight': latest['weight'],
            'latest_bmi': latest['bmi'],
            'avg_weight': round(sum(weights) / len(weights), 1),
            'min_weight': min(weights),
            'max_weight': max(weights),
            'trend': 'up' if len(weights) > 1 and weights[0] > weights[-1] else 'down' if len(weights) > 1 else 'stable',
            'record_count': len(history)
        }

    def _analyze_blood_pressure(self, history: List[Dict]) -> Dict[str, Any]:
        """分析血压数据"""
        if not history:
            return {'has_data': False}

        systolics = [h['systolic'] for h in history]
        diastolics = [h['diastolic'] for h in history]
        latest = history[0]

        return {
            'has_data': True,
            'latest_systolic': latest['systolic'],
            'latest_diastolic': latest['diastolic'],
            'latest_status': latest['status'],
            'avg_systolic': round(sum(systolics) / len(systolics)),
            'avg_diastolic': round(sum(diastolics) / len(diastolics)),
            'record_count': len(history)
        }

    def _analyze_exercise(self, history: List[Dict]) -> Dict[str, Any]:
        """分析运动数据"""
        if not history:
            return {'has_data': False}

        total_calories = sum(h['calories'] or 0 for h in history)
        total_duration = sum(h['duration_minutes'] or 0 for h in history)

        # 按运动类型统计
        type_stats = {}
        for h in history:
            et = h['exercise_type']
            if et not in type_stats:
                type_stats[et] = {'count': 0, 'duration': 0, 'calories': 0}
            type_stats[et]['count'] += 1
            type_stats[et]['duration'] += h['duration_minutes'] or 0
            type_stats[et]['calories'] += h['calories'] or 0

        return {
            'has_data': True,
            'total_calories': total_calories,
            'total_duration': total_duration,
            'exercise_days': len(history),
            'avg_duration': round(total_duration / len(history)) if history else 0,
            'type_stats': type_stats
        }

    def _analyze_sleep(self, history: List[Dict]) -> Dict[str, Any]:
        """分析睡眠数据"""
        if not history:
            return {'has_data': False}

        durations = [h['duration_hours'] for h in history]

        return {
            'has_data': True,
            'avg_duration': round(sum(durations) / len(durations), 1),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'record_count': len(history)
        }

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """生成健康建议"""
        recommendations = []

        # 体重建议
        weight = report.get('weight', {})
        if weight.get('has_data'):
            bmi = weight.get('latest_bmi', 0)
            if bmi > 24:
                recommendations.append('您的BMI偏高，建议适当控制饮食，增加运动量')
            elif bmi < 18.5:
                recommendations.append('您的BMI偏低，建议增加营养摄入，保持规律作息')

        # 血压建议
        bp = report.get('blood_pressure', {})
        if bp.get('has_data'):
            status = bp.get('latest_status', {})
            if status.get('level') in ['elevated', 'high']:
                recommendations.append('您的血压偏高，建议减少盐分摄入，定期监测血压，必要时就医')

        # 运动建议
        exercise = report.get('exercise', {})
        if exercise.get('has_data'):
            if exercise.get('exercise_days', 0) < 10:
                recommendations.append('建议每周运动3-5次，每次30分钟以上')
        else:
            recommendations.append('暂无运动记录，建议开始适量运动，如散步、慢跑等')

        # 睡眠建议
        sleep = report.get('sleep', {})
        if sleep.get('has_data'):
            avg = sleep.get('avg_duration', 0)
            if avg < 7:
                recommendations.append('您的平均睡眠时间不足7小时，建议早睡早起，保证充足睡眠')
            elif avg > 9:
                recommendations.append('您的睡眠时间偏长，建议保持规律作息')

        if not recommendations:
            recommendations.append('您的健康状况良好，请继续保持健康的生活方式')

        return recommendations


# 测试代码
if __name__ == '__main__':
    service = HealthProfileService()

    logger.info("=== 健康档案管理服务测试 ===\n")

    # 创建健康档案
    logger.info("1. 创建健康档案...")
    result = service.create_profile(
        member_name="测试用户",
        gender="male",
        birth_date="1990-01-15",
        height=175,
        blood_type="A"
    )
    logger.info(f"   结果：{result}\n")

    if result['success']:
        profile_id = result['profile_id']

        # 记录体重
        logger.info("2. 记录体重...")
        result = service.record_weight(profile_id, 70.5, "早餐前")
        logger.info(f"   结果：{result}\n")

        # 记录血压
        logger.info("3. 记录血压...")
        result = service.record_blood_pressure(profile_id, 120, 80, 72, "早晨测量")
        logger.info(f"   结果：{result}\n")

        # 记录运动
        logger.info("4. 记录运动...")
        result = service.record_exercise(profile_id, "running", 30, distance_km=5)
        logger.info(f"   结果：{result}\n")

        # 生成健康报告
        logger.info("5. 生成健康报告...")
        report = service.generate_health_report(profile_id)
        logger.info(f"   体重分析：{report.get('weight', {})}")
        logger.info(f"   血压分析：{report.get('blood_pressure', {})}")
        logger.info(f"   运动分析：{report.get('exercise', {})}")
        logger.info(f"   健康建议：{report.get('recommendations', [])}\n")

    logger.info("✅ 测试完成！")