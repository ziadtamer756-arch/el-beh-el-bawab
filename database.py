import sqlite3
from contextlib import contextmanager
from app.core.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """إنشاء ١٥ جدولاً متكاملاً في قاعدة البيانات تغطي الـ 15 APIs والـ 15 AI Agents."""
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. جدول العمارات (Buildings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                city TEXT NOT NULL DEFAULT 'القاهرة',
                invite_code TEXT UNIQUE NOT NULL,
                floors_count INTEGER NOT NULL DEFAULT 12,
                monthly_maintenance_fee REAL NOT NULL DEFAULT 300.0,
                water_pump_status TEXT NOT NULL DEFAULT 'normal',
                elevator_status TEXT NOT NULL DEFAULT 'operational',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. جدول المستخدمين (Users: resident, bawab, admin)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('resident', 'bawab', 'admin')),
                building_id INTEGER NOT NULL,
                apartment_number TEXT,
                floor_number INTEGER,
                is_available INTEGER NOT NULL DEFAULT 1,
                wallet_balance REAL NOT NULL DEFAULT 0.0,
                rating_avg REAL NOT NULL DEFAULT 5.0,
                rating_count INTEGER NOT NULL DEFAULT 1,
                otp_code TEXT DEFAULT '1234',
                device_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
            );
        """)

        # 3. جدول الطلبات والمشاوير (Orders)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                resident_id INTEGER NOT NULL,
                bawab_id INTEGER,
                category TEXT NOT NULL CHECK(category IN (
                    'groceries', 'pharmacy', 'errand', 'cleaning',
                    'car_wash', 'plumbing_electrical', 'luggage_help', 'other'
                )),
                title TEXT NOT NULL,
                details TEXT NOT NULL,
                urgency TEXT NOT NULL DEFAULT 'normal' CHECK(urgency IN ('normal', 'urgent', 'scheduled')),
                scheduled_time TEXT,
                status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN (
                    'pending', 'accepted', 'in_progress', 'delivered', 'cancelled'
                )),
                estimated_items_cost REAL DEFAULT 0.0,
                actual_items_cost REAL DEFAULT 0.0,
                service_tip REAL DEFAULT 15.0,
                payment_method TEXT NOT NULL DEFAULT 'cash' CHECK(payment_method IN ('cash', 'instapay', 'wallet')),
                is_paid INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                ai_parsed_items TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (resident_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (bawab_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        # 4. جدول إعلانات العمارة (Announcements)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'normal',
                is_pinned INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 5. جدول المعاملات المالية والعهدة (Wallet Transactions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallet_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                order_id INTEGER,
                tx_type TEXT NOT NULL CHECK(tx_type IN ('tip', 'reimbursement', 'topup', 'maintenance_fee', 'settlement')),
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL DEFAULT 'cash',
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL
            );
        """)

        # 6. جدول التقييمات والمراجعات (Reviews)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER UNIQUE NOT NULL,
                resident_id INTEGER NOT NULL,
                bawab_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (resident_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (bawab_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 7. جدول الإشعارات الفورية (Notifications)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notif_type TEXT NOT NULL DEFAULT 'order_update',
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 8. جدول الصيانة والأعطال المنزلية (Maintenance Tickets - API #5)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                resident_id INTEGER NOT NULL,
                specialty TEXT NOT NULL CHECK(specialty IN ('plumbing', 'electrical', 'carpentry', 'gas', 'elevator', 'satellite_internet', 'ac')),
                issue_title TEXT NOT NULL,
                description TEXT NOT NULL,
                urgency TEXT NOT NULL DEFAULT 'normal',
                status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'assigned', 'in_progress', 'resolved')),
                assigned_technician TEXT,
                estimated_cost REAL DEFAULT 0.0,
                ai_diagnosis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (resident_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 9. جدول تصاريح الزوار والدليفري والأمن (Visitors & Gate Security - API #6)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visitors_passes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                resident_id INTEGER NOT NULL,
                visitor_name TEXT NOT NULL,
                visitor_type TEXT NOT NULL CHECK(visitor_type IN ('guest', 'delivery', 'technician', 'broker')),
                pass_code TEXT NOT NULL,
                expected_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'expected' CHECK(status IN ('expected', 'arrived', 'departed', 'denied')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (resident_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 10. جدول استلام الطرود وأمانات البوابة (Parcels & Deliveries - API #7)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parcels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                resident_id INTEGER NOT NULL,
                bawab_id INTEGER,
                courier_name TEXT NOT NULL,
                tracking_Or_desc TEXT NOT NULL,
                cod_amount REAL DEFAULT 0.0,
                paid_by_bawab INTEGER NOT NULL DEFAULT 0,
                pickup_code TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'at_gate' CHECK(status IN ('at_gate', 'delivered_to_apt')),
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (resident_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 11. جدول الجراج واشتراكات غسيل السيارات (Garage & Car Care - API #8)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                resident_id INTEGER NOT NULL,
                car_model TEXT NOT NULL,
                plate_number TEXT NOT NULL,
                parking_spot TEXT NOT NULL,
                wash_schedule TEXT NOT NULL DEFAULT 'الأحد والأربعاء 7:00 ص',
                key_with_bawab INTEGER NOT NULL DEFAULT 1,
                last_wash_status TEXT NOT NULL DEFAULT 'تم الغسيل ✅',
                monthly_fee REAL DEFAULT 200.0,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (resident_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 12. جدول المرافق المشتركة وقراءات العدادات (Utilities & Meters - API #9)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utility_bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                utility_type TEXT NOT NULL CHECK(utility_type IN ('water_shared', 'elevator_electricity', 'stairs_cleaning', 'gas_cylinder', 'garbage_collection')),
                month_label TEXT NOT NULL,
                total_amount REAL NOT NULL,
                per_apartment_share REAL NOT NULL,
                paid_apartments_count INTEGER NOT NULL DEFAULT 8,
                status TEXT NOT NULL DEFAULT 'collecting',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
            );
        """)

        # 13. جدول الدردشة والرسائل الصوتية (Chat Messages - API #13)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                is_voice_note INTEGER NOT NULL DEFAULT 0,
                ai_quick_replies TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 14. جدول بلاغات الطوارئ والاستغاثة (Emergency SOS - API #14)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emergency_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                reporter_id INTEGER NOT NULL,
                emergency_type TEXT NOT NULL CHECK(emergency_type IN ('elevator_stuck', 'gas_leak', 'water_burst', 'medical_help', 'security_alert')),
                apartment_or_location TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'responding', 'resolved')),
                ai_action_plan TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 15. جدول سجل عمليات الـ 15 AI Agents (AI Agent Execution Logs - API #15)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL DEFAULT 1,
                agent_id TEXT NOT NULL,
                agent_name_ar TEXT NOT NULL,
                input_query TEXT NOT NULL,
                output_summary TEXT NOT NULL,
                confidence_score REAL NOT NULL DEFAULT 0.96,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("SELECT COUNT(*) as count FROM buildings;")
        if cursor.fetchone()["count"] == 0:
            _seed_initial_data(cursor)


def _seed_initial_data(cursor: sqlite3.Cursor) -> None:
    """إدخال بيانات تجريبية شاملة لجميع الجداول الـ ١٥."""
    cursor.execute("""
        INSERT INTO buildings (name, address, city, invite_code, floors_count, monthly_maintenance_fee, water_pump_status, elevator_status)
        VALUES ('عمارة النيل الذهبية', '١٥ شارع التحرير - الدقي', 'الجيزة', 'NILE-15', 12, 300.0, 'تعمل بكفاءة (ضغط ممتاز)', 'يعمل (صيانة دورية الثلاثاء)');
    """)
    building_id = cursor.lastrowid

    # إضافة البواب (عم عبد السميع)
    cursor.execute("""
        INSERT INTO users (full_name, phone, role, building_id, apartment_number, floor_number, is_available, wallet_balance, rating_avg, rating_count)
        VALUES ('عم عبد السميع (البيه البواب)', '01000000001', 'bawab', ?, 'غرفة الحارس - الأرضي', 0, 1, 540.0, 4.9, 24);
    """, (building_id,))
    bawab_id = cursor.lastrowid

    # إضافة سكان
    cursor.execute("""
        INSERT INTO users (full_name, phone, role, building_id, apartment_number, floor_number, is_available, wallet_balance)
        VALUES
        ('أستاذ أحمد زكي', '01000000002', 'resident', ?, 'شقة 12', 4, 1, 350.0),
        ('مدام سعاد', '01000000003', 'resident', ?, 'شقة 20', 7, 1, 180.0),
        ('مهندس طارق علام', '01000000004', 'resident', ?, 'شقة 5', 2, 1, 500.0);
    """, (building_id, building_id, building_id))

    cursor.execute("SELECT id FROM users WHERE phone = '01000000002';")
    res1 = cursor.fetchone()["id"]
    cursor.execute("SELECT id FROM users WHERE phone = '01000000003';")
    res2 = cursor.fetchone()["id"]
    cursor.execute("SELECT id FROM users WHERE phone = '01000000004';")
    res3 = cursor.fetchone()["id"]

    # طلبات تجريبية
    cursor.execute("""
        INSERT INTO orders (
            building_id, resident_id, bawab_id, category, title, details,
            urgency, status, estimated_items_cost, actual_items_cost, service_tip, payment_method, is_paid, notes
        ) VALUES
        (?, ?, ?, 'groceries', 'طلبات سوبرماركت ومخبز', '٢ لبن جهينة كامل الدسم + ١٠ عيش بلدي سخن + كرتونة بيض أحمر', 'urgent', 'in_progress', 220.0, 225.0, 25.0, 'instapay', 0, 'هات العيش طازة من فرن التحرير'),
        (?, ?, NULL, 'plumbing_electrical', 'تغيير أنبوبة البوتاجاز وفحص المنظم', 'محتاجين حد يغير الأنبوبة ويبص على جلدة المنظم في المطبخ', 'urgent', 'pending', 150.0, 0.0, 35.0, 'cash', 0, 'رن الجرس مرة واحدة'),
        (?, ?, ?, 'car_wash', 'غسيل العربية قبل الساعة ٨:٣٠ الصبح', 'العربية راكنة قدام البوابة الرئيسية - كيا سيراتو فضي', 'scheduled', 'accepted', 0.0, 0.0, 50.0, 'wallet', 1, 'المفتاح معاك في الأمانات'),
        (?, ?, ?, 'pharmacy', 'أدوية من صيدلية العزبي', 'علبة بنادول إكسترا + فيتامين سي فوار + قطرة عين', 'normal', 'delivered', 145.0, 140.0, 20.0, 'instapay', 1, 'تم التسليم عند الباب');
    """, (
        building_id, res1, bawab_id,
        building_id, res2,
        building_id, res1, bawab_id,
        building_id, res3, bawab_id,
    ))

    # تذاكر صيانة (API #5)
    cursor.execute("""
        INSERT INTO maintenance_tickets (building_id, resident_id, specialty, issue_title, description, urgency, status, assigned_technician, estimated_cost, ai_diagnosis)
        VALUES
        (?, ?, 'plumbing', 'تسريب مياه تحت حوض المطبخ', 'في تنقيط مستمر من ليّ الخلاط البارد تحت الحوض', 'urgent', 'assigned', 'الأسطى حسن السباك (بإشراف عم عبد السميع)', 180.0, 'تشخيص الذكاء الاصطناعي: تلف في جلدة الوصلة المرنة (الليّ) أو محبس الزاوية؛ يحتاج مفتاح فرنساوي ووصلة نص بوصة.'),
        (?, ?, 'elevator', 'صوت صفير في باب الأسانسير بالدور الرابع', 'الباب بيقفل ببطء وبيعمل صوت احتكاك بسيط', 'normal', 'open', 'شركة النيل للمصاعد', 0.0, 'تشخيص الذكاء الاصطناعي: يحتاج تشحيم مجرى الباب وضبط حساس الإغلاق.');
    """, (building_id, res1, building_id, res2))

    # تصاريح الزوار والدليفري (API #6)
    cursor.execute("""
        INSERT INTO visitors_passes (building_id, resident_id, visitor_name, visitor_type, pass_code, expected_time, status, notes)
        VALUES
        (?, ?, 'مندوب طلبات مارت (Talabat)', 'delivery', 'PASS-482', 'خلال ١٥ دقيقة', 'expected', 'خليه يطلع الدور الرابع شقة 12'),
        (?, ?, 'أستاذ كريم محمود (ضيف عائلي)', 'guest', 'PASS-910', 'اليوم ٠٨:٠٠ مساءً', 'expected', 'افتحله بوابة الجراج يا عم عبد السميع');
    """, (building_id, res1, building_id, res3))

    # أمانات البوابة والطرود (API #7)
    cursor.execute("""
        INSERT INTO parcels (building_id, resident_id, bawab_id, courier_name, tracking_Or_desc, cod_amount, paid_by_bawab, pickup_code, status)
        VALUES
        (?, ?, ?, 'أمازون مصر (Amazon)', 'طرد كرتونة متوسطة - شقة 12', 320.0, 1, 'BOX-12', 'at_gate'),
        (?, ?, ?, 'بوسطة (Bosta)', 'شحنة ملابس مدفوعة مسبقاً - شقة 20', 0.0, 0, 'BOX-20', 'at_gate');
    """, (building_id, res1, bawab_id, building_id, res2, bawab_id))

    # سيارات الجراج (API #8)
    cursor.execute("""
        INSERT INTO vehicles (building_id, resident_id, car_model, plate_number, parking_spot, wash_schedule, key_with_bawab, last_wash_status, monthly_fee)
        VALUES
        (?, ?, 'كيا سيراتو فضي', 'أ ب ج ٤٥٢١', 'باكية رقم 4', 'الأحد والأربعاء ٧:٠٠ ص', 1, 'تم الغسيل والتلميع صباح اليوم ✨', 250.0),
        (?, ?, 'هيونداي توسان أسود', 'س ص ع ٨٩١٢', 'باكية رقم 9', 'الإثنين والخميس ٨:٠٠ ص', 1, 'مجدول غداً صباحاً ⏰', 300.0);
    """, (building_id, res1, building_id, res3))

    # فواتير المرافق المشتركة (API #9)
    cursor.execute("""
        INSERT INTO utility_bills (building_id, utility_type, month_label, total_amount, per_apartment_share, paid_apartments_count, status)
        VALUES
        (?, 'water_shared', 'أكتوبر ٢٠٢٦ - مياه وموتور العمارة', 2400.0, 100.0, 19, 'collecting'),
        (?, 'elevator_electricity', 'أكتوبر ٢٠٢٦ - كهرباء وصيانة الأسانسير', 4800.0, 200.0, 21, 'collecting');
    """, (building_id, building_id))

    # رسائل الدردشة (API #13)
    cursor.execute("""
        INSERT INTO chat_messages (building_id, sender_id, receiver_id, message_text, is_voice_note, ai_quick_replies)
        VALUES
        (?, ?, ?, 'صباح الخير يا عم عبد السميع، لو نزلت الفرن هاتلي بـ ٢٠ جنيه عيش سخن معاك', 0, '["حاضر يا بيه فوراً","أنا في الفرن حالياً","دقيقتين وأطلعلك"]'),
        (?, ?, ?, 'صباح الفل يا أستاذ أحمد، عنيا الاتنين أنا قدام الفرن أهو وهطلعهم لشقة ١٢ على طول.', 0, '["تسلم إيدك","حسابهم على إنستا باي","شكراً يا عم عبد السميع"]');
    """, (building_id, res1, bawab_id, building_id, bawab_id, res1))

    # معاملات المحفظة
    cursor.execute("""
        INSERT INTO wallet_transactions (building_id, user_id, order_id, tx_type, amount, payment_method, description)
        VALUES
        (?, ?, 4, 'reimbursement', 140.0, 'instapay', 'سداد فاتورة صيدلية العزبي - شقة 5'),
        (?, ?, 4, 'tip', 20.0, 'instapay', 'إكرامية توصيل طلب صيدلية - شقة 5'),
        (?, ?, NULL, 'reimbursement', 320.0, 'cash', 'عهدة طرد أمازون مدفوع بواسطة البواب - شقة 12'),
        (?, ?, NULL, 'maintenance_fee', 300.0, 'instapay', 'تحصيل اشتراك صيانة العمارة الشهري - شقة 12');
    """, (building_id, bawab_id, building_id, bawab_id, building_id, bawab_id, building_id, res1))

    # إعلانات العمارة
    cursor.execute("""
        INSERT INTO announcements (building_id, author_id, title, content, priority, is_pinned)
        VALUES
        (?, ?, 'تنبيه هام: صيانة الأسانسير غداً الثلاثاء', 'سيتم إيقاف الأسانسير غداً من الساعة ١٠ صباحاً حتى ١٢ ظهراً للصيانة الدورية. لو حد محتاج طلبات تقيلة يبلغ عم عبد السميع بدري.', 'urgent', 1),
        (?, ?, 'موعد غسيل وتعقيم خزان المياه العلوي', 'يوم الجمعة القادم الساعة ٨ صباحاً سيتم تنظيف وتعقيم خزان المياه بالتعاون مع شركة متخصصة.', 'normal', 0);
    """, (building_id, bawab_id, building_id, bawab_id))

    # تقييم أولي
    cursor.execute("""
        INSERT INTO reviews (order_id, resident_id, bawab_id, rating, comment)
        VALUES (4, ?, ?, 5, 'تسلم إيدك يا عم عبد السميع، جبت الدواء في أقل من ربع ساعة!');
    """, (res3, bawab_id))

    # سجل أولي لعمليات الـ AI Agents
    cursor.execute("""
        INSERT INTO ai_agent_logs (building_id, agent_id, agent_name_ar, input_query, output_summary, confidence_score)
        VALUES
        (1, 'agent_01_order_parser', 'وكيل تحليل الطلبات باللهجة المصرية', 'عايز ٢ لبن جهينة وكرتونة بيض وعيش سخن من الفرن', 'تم استخراج ٣ أصناف (لبن جهينة ×٢، بيض أحمر ×١، عيش بلدي ×١٠) وتقدير التكلفة بـ ٢٢٠ ج.م والأولوية: مستعجل.', 0.98),
        (1, 'agent_03_errand_batcher', 'وكيل تجميع المشاوير الذكي للبواب', 'تجميع طلبات الدور الرابع والسابع', 'تم دمج طلب شقة ١٢ وطلب شقة ٢٠ في مشوار واحد لمنطقة التحرير لتوفير ٢٥ دقيقة لعم عبد السميع.', 0.95);
    """)
