
import json
import os
import time
import random
from datetime import datetime, timedelta
from data_utils import load_data, save_data

TASKS_FILE = "user_tasks.json"

class TasksSystem:
    def __init__(self):
        self.tasks_file = TASKS_FILE
        self.task_templates = {
            # مهام يومية
            "daily_work": {
                "name": "عامل مجتهد",
                "description": "قم بالعمل 3 مرات",
                "type": "work",
                "target": 3,
                "category": "daily",
                "difficulty": "سهل",
                "reward": {"دولار": 50000, "exp": 100},
                "duration_hours": 24
            },
            "daily_shop": {
                "name": "متسوق نشط",
                "description": "اشتر 5 عناصر من المتجر",
                "type": "buy_items",
                "target": 5,
                "category": "daily",
                "difficulty": "سهل",
                "reward": {"دولار": 30000, "exp": 75},
                "duration_hours": 24
            },
            "collect_gold": {
                "name": "جامع الذهب",
                "description": "اجمع 50 قطعة ذهب",
                "type": "collect_gold",
                "target": 50,
                "category": "daily",
                "difficulty": "متوسط",
                "reward": {"ذهب": 25, "exp": 150},
                "duration_hours": 24
            },
            "harvest_crops": {
                "name": "مزارع ماهر",
                "description": "احصد 10 محاصيل",
                "type": "harvest_crops",
                "target": 10,
                "category": "daily",
                "difficulty": "متوسط",
                "reward": {"دولار": 40000, "exp": 120},
                "duration_hours": 24
            },
            "win_games": {
                "name": "لاعب محترف",
                "description": "اربح 5 ألعاب",
                "type": "win_games",
                "target": 5,
                "category": "daily",
                "difficulty": "صعب",
                "reward": {"دولار": 60000, "ماس": 2, "exp": 200},
                "duration_hours": 24
            },
            "daily_trade": {
                "name": "متداول يومي",
                "description": "قم بـ 3 عمليات تداول",
                "type": "trade_count",
                "target": 3,
                "category": "daily",
                "difficulty": "متوسط",
                "reward": {"دولار": 40000, "exp": 110},
                "duration_hours": 24
            },
            "daily_fishing": {
                "name": "صياد ماهر",
                "description": "اصطد 8 أسماك",
                "type": "catch_fish",
                "target": 8,
                "category": "daily",
                "difficulty": "متوسط",
                "reward": {"دولار": 35000, "ذهب": 20, "exp": 90},
                "duration_hours": 24
            },
            
            # مهام أسبوعية
            "weekly_wealth": {
                "name": "جامع الثروات",
                "description": "اربح مليون دولار",
                "type": "earn_money",
                "target": 1000000,
                "category": "weekly",
                "difficulty": "صعب جداً",
                "reward": {"دولار": 500000, "ذهب": 100, "ماس": 10, "exp": 1000},
                "duration_hours": 168
            },
            "weekly_trader": {
                "name": "تاجر محنك",
                "description": "قم بـ 20 عملية تداول",
                "type": "trade_count",
                "target": 20,
                "category": "weekly",
                "difficulty": "صعب",
                "reward": {"دولار": 300000, "ذهب": 50, "exp": 500},
                "duration_hours": 168
            },
            "weekly_farmer": {
                "name": "مزارع أسطوري",
                "description": "احصد 100 محصول",
                "type": "harvest_crops",
                "target": 100,
                "category": "weekly",
                "difficulty": "صعب جداً",
                "reward": {"دولار": 800000, "ذهب": 80, "ماس": 5, "exp": 800},
                "duration_hours": 168
            }
        }

    def load_user_tasks(self, user_id):
        """تحميل مهام المستخدم"""
        if not os.path.exists(self.tasks_file):
            return {"active_tasks": [], "completed_tasks": [], "last_update": 0}
        
        with open(self.tasks_file, "r", encoding="utf-8") as f:
            all_tasks = json.load(f)
        
        return all_tasks.get(str(user_id), {"active_tasks": [], "completed_tasks": [], "last_update": 0})

    def save_user_tasks(self, user_id, tasks_data):
        """حفظ مهام المستخدم"""
        if not os.path.exists(self.tasks_file):
            all_tasks = {}
        else:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                all_tasks = json.load(f)
        
        all_tasks[str(user_id)] = tasks_data
        
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(all_tasks, f, ensure_ascii=False, indent=4)

    def generate_daily_tasks(self, user_id):
        """توليد مهام يومية جديدة"""
        daily_templates = [t for t in self.task_templates.values() if t["category"] == "daily"]
        selected_tasks = random.sample(daily_templates, min(3, len(daily_templates)))
        
        tasks = []
        current_time = time.time()
        
        for i, template in enumerate(selected_tasks):
            task = {
                "id": f"daily_{int(current_time)}_{random.randint(1000, 9999)}",
                "name": template["name"],
                "description": template["description"],
                "type": template["type"],
                "target": template["target"],
                "progress": 0,
                "category": template["category"],
                "difficulty": template["difficulty"],
                "reward": template["reward"].copy(),
                "created_at": current_time,
                "expires_at": current_time + (template["duration_hours"] * 3600),
                "completed": False,
                "claimed": False
            }
            tasks.append(task)
        
        return tasks

    def generate_weekly_tasks(self, user_id):
        """توليد مهام أسبوعية جديدة"""
        weekly_templates = [t for t in self.task_templates.values() if t["category"] == "weekly"]
        selected_tasks = random.sample(weekly_templates, min(2, len(weekly_templates)))
        
        tasks = []
        current_time = time.time()
        
        for template in selected_tasks:
            task = {
                "id": f"{user_id}_{template['type']}_weekly_{int(current_time)}",
                "name": template["name"],
                "description": template["description"],
                "type": template["type"],
                "target": template["target"],
                "progress": 0,
                "category": template["category"],
                "difficulty": template["difficulty"],
                "reward": template["reward"].copy(),
                "created_at": current_time,
                "expires_at": current_time + (template["duration_hours"] * 3600),
                "completed": False,
                "claimed": False
            }
            tasks.append(task)
        
        return tasks

    def check_and_update_tasks(self, user_id):
        """فحص وتحديث مهام المستخدم"""
        user_tasks = self.load_user_tasks(user_id)
        current_time = time.time()
        
        # إزالة المهام المنتهية الصلاحية
        active_tasks = [task for task in user_tasks["active_tasks"] if task["expires_at"] > current_time]
        
        # فحص الحاجة لمهام جديدة
        daily_tasks = [task for task in active_tasks if task["category"] == "daily"]
        weekly_tasks = [task for task in active_tasks if task["category"] == "weekly"]
        
        # توليد مهام يومية إذا لم تكن موجودة
        if len(daily_tasks) < 3:
            new_daily = self.generate_daily_tasks(user_id)
            active_tasks.extend(new_daily)
        
        # توليد مهام أسبوعية إذا لم تكن موجودة
        if len(weekly_tasks) < 2:
            new_weekly = self.generate_weekly_tasks(user_id)
            active_tasks.extend(new_weekly)
        
        user_tasks["active_tasks"] = active_tasks
        user_tasks["last_update"] = current_time
        self.save_user_tasks(user_id, user_tasks)

    def update_task_progress(self, user_id, task_type, amount=1):
        """تحديث تقدم المهام"""
        user_tasks = self.load_user_tasks(user_id)
        completed_tasks = []
        
        for task in user_tasks["active_tasks"]:
            if task["type"] == task_type and not task["completed"]:
                task["progress"] = min(task["progress"] + amount, task["target"])
                
                if task["progress"] >= task["target"]:
                    task["completed"] = True
                    completed_tasks.append(task)
        
        self.save_user_tasks(user_id, user_tasks)
        return completed_tasks

    def claim_task_reward(self, user_id, task_id):
        """استلام مكافأة المهمة"""
        user_tasks = self.load_user_tasks(user_id)
        
        for task in user_tasks["active_tasks"]:
            if task["id"] == task_id and task["completed"] and not task.get("claimed", False):
                # إضافة المكافآت
                data = load_data()
                user = data[str(user_id)]
                
                reward = task["reward"]
                for currency, amount in reward.items():
                    if currency in ["دولار", "ذهب", "ماس"]:
                        user["balance"][currency] = user["balance"].get(currency, 0) + amount
                    elif currency == "exp":
                        user["experience"] = user.get("experience", 0) + amount
                        self._update_experience_level(user)
                
                save_data(data)
                
                # تسجيل المهمة كمُستلمة
                task["claimed"] = True
                
                # نقل إلى المهام المكتملة
                user_tasks["completed_tasks"].append(task)
                user_tasks["active_tasks"].remove(task)
                
                self.save_user_tasks(user_id, user_tasks)
                return reward
        
        return None

    def _update_experience_level(self, user):
        """تحديث مستوى المستخدم حسب الخبرة"""
        exp = user.get("experience", 0)
        current_level = user.get("level", 1)
        
        # حساب المستوى الجديد
        new_level = 1
        total_exp_needed = 0
        
        while total_exp_needed <= exp:
            total_exp_needed += (new_level * 1000)
            if exp >= total_exp_needed:
                new_level += 1
            else:
                break
        
        if new_level > current_level:
            user["level"] = new_level

    def get_user_level_info(self, user_id):
        """جلب معلومات مستوى المستخدم"""
        data = load_data()
        user = data.get(str(user_id), {})
        
        exp = user.get("experience", 0)
        level = user.get("level", 1)
        
        # حساب الخبرة المطلوبة للمستوى التالي
        exp_for_current_level = sum(i * 1000 for i in range(1, level))
        exp_for_next_level = level * 1000
        exp_progress = exp - exp_for_current_level
        exp_needed = exp_for_next_level - exp_progress
        
        return {
            "level": level,
            "experience": exp,
            "exp_progress": max(0, exp_progress),
            "exp_for_next_level": exp_for_next_level,
            "exp_needed": max(0, exp_needed)
        }

# إنشاء مثيل من النظام
tasks_system = TasksSystem()
