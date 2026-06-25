from app import app, db, User, Delivery, Payment, PriceConfig, Notification
from datetime import datetime, timedelta
import random

def populate_farmers_and_deliveries():
    with app.app_context():
        # Clear existing data (optional - comment out if you want to keep existing)
        print("Clearing existing data...")
        Delivery.query.delete()
        Payment.query.delete()
        Notification.query.delete()
        User.query.filter_by(role='farmer').delete()
        db.session.commit()
        
        # Kenyan names for farmers
        farmer_data = [
            # Kalenjin names
            ("Kiprono", "Cheruiyot", "+254712000001"),
            ("Kipchumba", "Kemboi", "+254712000002"),
            ("Chepkoech", "Rotich", "+254712000003"),
            ("Jepkemoi", "Kipruto", "+254712000004"),
            ("Kipngetich", "Bett", "+254712000005"),
            ("Chebet", "Kiprotich", "+254712000006"),
            ("Kiptanui", "Kimutai", "+254712000007"),
            ("Jepchirchir", "Koech", "+254712000008"),
            ("Kipkemboi", "Tanui", "+254712000009"),
            ("Chepngeno", "Kiplagat", "+254712000010"),
            
            # Kikuyu names
            ("Kamau", "Njoroge", "+254713000001"),
            ("Wanjiku", "Wambui", "+254713000002"),
            ("Njeri", "Mwangi", "+254713000003"),
            ("Wanjiru", "Kamande", "+254713000004"),
            ("Nyambura", "Gathogo", "+254713000005"),
            ("Muthoni", "Ndung'u", "+254713000006"),
            ("Wambui", "Kariuki", "+254713000007"),
            ("Njoki", "Maina", "+254713000008"),
            ("Wangari", "Macharia", "+254713000009"),
            ("Mumbi", "Gitonga", "+254713000010"),
            
            # Luo names
            ("Otieno", "Omondi", "+254714000001"),
            ("Achieng", "Odhiambo", "+254714000002"),
            ("Ochieng", "Okoth", "+254714000003"),
            ("Adhiambo", "Owino", "+254714000004"),
            ("Onyango", "Oluoch", "+254714000005"),
            ("Akinyi", "Obonyo", "+254714000006"),
            ("Odhiambo", "Onyango", "+254714000007"),
            ("Atieno", "Ogolla", "+254714000008"),
            ("Owuor", "Opiyo", "+254714000009"),
            ("Awino", "Otieno", "+254714000010"),
            
            # Luhya names
            ("Wafula", "Wekesa", "+254715000001"),
            ("Nasimiyu", "Wanjala", "+254715000002"),
            ("Wamalwa", "Simiyu", "+254715000003"),
            ("Nekesa", "Barasa", "+254715000004"),
            ("Wanjala", "Wafula", "+254715000005"),
            ("Nanjala", "Wamalwa", "+254715000006"),
            ("Sikuku", "Wekesa", "+254715000007"),
            ("Nelima", "Simiyu", "+254715000008"),
            ("Barasa", "Wanjala", "+254715000009"),
            ("Naliaka", "Wafula", "+254715000010"),
            
            # Kamba names
            ("Mutuku", "Muthoka", "+254716000001"),
            ("Mueni", "Kioko", "+254716000002"),
            ("Muthama", "Mutua", "+254716000003"),
            ("Kalekye", "Musyoka", "+254716000004"),
            ("Mutua", "Mwikali", "+254716000005"),
            ("Mwikali", "Mutuku", "+254716000006"),
            ("Musyoka", "Muthama", "+254716000007"),
            ("Kamene", "Mutua", "+254716000008"),
            ("Kioko", "Muthoka", "+254716000009"),
            ("Mutheu", "Musyoka", "+254716000010"),
            
            # Kisii names
            ("Ongeri", "Nyambane", "+254717000001"),
            ("Kerubo", "Momanyi", "+254717000002"),
            ("Nyambane", "Ongeri", "+254717000003"),
            ("Kwamboka", "Ongwae", "+254717000004"),
            ("Momanyi", "Kerubo", "+254717000005"),
            ("Moraa", "Nyakundi", "+254717000006"),
            ("Nyakundi", "Ongeri", "+254717000007"),
            ("Bosibori", "Momanyi", "+254717000008"),
            ("Ongwae", "Kerubo", "+254717000009"),
            ("Kemunto", "Nyambane", "+254717000010"),
            
            # Meru names
            ("Mwirigi", "Muthuri", "+254718000001"),
            ("Nkirote", "Mugambi", "+254718000002"),
            ("Mugambi", "Gitonga", "+254718000003"),
            ("Kanana", "Murithi", "+254718000004"),
            ("Murithi", "Mwirigi", "+254718000005"),
            ("Gacheri", "Mugambi", "+254718000006"),
            ("Gitonga", "Muthuri", "+254718000007"),
            ("Karimi", "Murithi", "+254718000008"),
            ("Muthuri", "Mwirigi", "+254718000009"),
            ("Ntinyari", "Gitonga", "+254718000010"),
            
            # Mijikenda names
            ("Katana", "Ngumbao", "+254719000001"),
            ("Nyevu", "Kazungu", "+254719000002"),
            ("Kazungu", "Charo", "+254719000003"),
            ("Nyota", "Katana", "+254719000004"),
            ("Charo", "Ngumbao", "+254719000005"),
            ("Nyang'anyi", "Kazungu", "+254719000006"),
            ("Ngumbao", "Katana", "+254719000007"),
            ("Zawadi", "Charo", "+254719000008"),
            ("Baya", "Kazungu", "+254719000009"),
            ("Riziki", "Ngumbao", "+254719000010"),
            
            # Additional diverse names
            ("Abdullahi", "Hassan", "+254720000001"),
            ("Fatuma", "Mohammed", "+254720000002"),
            ("Ahmed", "Ibrahim", "+254720000003"),
            ("Amina", "Omar", "+254720000004"),
            ("Mwangi", "Kimani", "+254720000005"),
            ("Njeri", "Githinji", "+254720000006"),
            ("Omondi", "Okello", "+254720000007"),
            ("Anyango", "Oduor", "+254720000008"),
            ("Wanjiku", "Ndungu", "+254720000009"),
            ("Kamau", "Thuo", "+254720000010"),
        ]
        
        # Collection centers in Kenya
        collection_centers = [
            "Nyeri Coffee Mill", "Kiambu Collection Center", "Murang'a Factory",
            "Kirinyaga Central", "Embu Coffee Works", "Meru Central Mill",
            "Machakos Collection Point", "Kisii Highlands Center", "Bungoma West Mill",
            "Nandi Hills Center", "Kericho Tea & Coffee", "Nakuru Processing",
            "Eldoret Collection", "Kisumu Lakeside Mill", "Mombasa Port Center"
        ]
        
        quality_grades = ['Premium', 'A', 'B', 'C']
        grade_weights = [0.15, 0.35, 0.35, 0.15]  # Distribution weights
        
        farmers_list = []
        
        print("Creating 100 farmers...")
        for idx, (first_name, last_name, phone) in enumerate(farmer_data, start=1):
            full_name = f"{first_name} {last_name}"
            username = f"{first_name.lower()}{idx}"
            membership = f"FARM{idx:04d}"
            password = f"farmer{idx}"
            
            farmer = User(
                username=username,
                full_name=full_name,
                phone=phone,
                membership_number=membership,
                role='farmer',
                is_active=True,
                email=f"{first_name.lower()}.{last_name.lower()}@coffee.co.ke"
            )
            farmer.set_password(password)
            db.session.add(farmer)
            farmers_list.append(farmer)
            
            if idx % 20 == 0:
                print(f"Created {idx} farmers...")
        
        db.session.commit()
        print("✅ 100 farmers created successfully!")
        
        # Create deliveries for each farmer
        print("\nCreating delivery records...")
        start_date = datetime.now() - timedelta(days=365)  # Start from 1 year ago
        
        total_deliveries = 0
        for farmer in farmers_list:
            # Each farmer has 10-50 deliveries over the year
            num_deliveries = random.randint(10, 50)
            
            for _ in range(num_deliveries):
                # Random date within the last year
                days_ago = random.randint(1, 365)
                delivery_date = datetime.now() - timedelta(days=days_ago)
                delivery_date = delivery_date.replace(
                    hour=random.randint(7, 17),
                    minute=random.randint(0, 59)
                )
                
                # Random quantity based on quality
                grade = random.choices(quality_grades, weights=grade_weights)[0]
                
                if grade == 'Premium':
                    quantity = round(random.uniform(10, 50), 1)
                elif grade == 'A':
                    quantity = round(random.uniform(20, 100), 1)
                elif grade == 'B':
                    quantity = round(random.uniform(30, 150), 1)
                else:
                    quantity = round(random.uniform(40, 200), 1)
                
                unit = 'kg'
                collection_center = random.choice(collection_centers)
                
                delivery = Delivery(
                    farmer_id=farmer.id,
                    date_delivered=delivery_date,
                    quantity=quantity,
                    unit=unit,
                    quality_grade=grade,
                    collection_center=collection_center,
                    recorded_by=2  # Staff ID 2
                )
                db.session.add(delivery)
                
                # Calculate payment
                price_config = PriceConfig.query.filter_by(quality_grade=grade).first()
                if price_config:
                    amount = quantity * price_config.price_per_unit
                    deduction_percent = random.uniform(0, 5)  # 0-5% deductions
                    deductions = round(amount * deduction_percent / 100, 2)
                    net_payment = round(amount - deductions, 2)
                    
                    # Random payment status
                    status = random.choices(['paid', 'pending'], weights=[0.8, 0.2])[0]
                    
                    payment = Payment(
                        farmer_id=farmer.id,
                        amount_earned=amount,
                        deductions=deductions,
                        net_payment=net_payment,
                        payment_date=delivery_date + timedelta(days=random.randint(1, 14)),
                        status=status
                    )
                    db.session.add(payment)
                
                total_deliveries += 1
                
                if total_deliveries % 500 == 0:
                    db.session.commit()
                    print(f"Created {total_deliveries} deliveries...")
        
        db.session.commit()
        print(f"✅ {total_deliveries} deliveries created successfully!")
        
        # Create notifications for recent deliveries
        print("\nCreating notifications...")
        recent_deliveries = Delivery.query.filter(
            Delivery.date_delivered >= datetime.now() - timedelta(days=7)
        ).all()
        
        for delivery in recent_deliveries:
            notification = Notification(
                user_id=delivery.farmer_id,
                title="New Delivery Recorded",
                content=f"Your delivery of {delivery.quantity} kg Grade {delivery.quality_grade} coffee has been recorded at {delivery.collection_center}.",
                type="delivery"
            )
            db.session.add(notification)
        
        db.session.commit()
        print("✅ Notifications created successfully!")
        
        # Print summary
        print("\n" + "="*50)
        print("📊 DATABASE POPULATION SUMMARY")
        print("="*50)
        print(f"👨‍🌾 Total Farmers: {len(farmers_list)}")
        print(f"📦 Total Deliveries: {total_deliveries}")
        print(f"💰 Total Payments: {Payment.query.count()}")
        print(f"🔔 Total Notifications: {Notification.query.count()}")
        
        # Calculate totals
        total_kg = db.session.query(db.func.sum(Delivery.quantity)).scalar() or 0
        total_value = db.session.query(db.func.sum(Payment.amount_earned)).scalar() or 0
        
        print(f"☕ Total Coffee Delivered: {total_kg:,.1f} kg")
        print(f"💵 Total Value: KSh {total_value:,.2f}")
        print("="*50)
        
        # Print sample farmer logins
        print("\n📋 SAMPLE FARMER LOGIN CREDENTIALS:")
        print("-"*50)
        for farmer in farmers_list[:5]:
            print(f"Username: {farmer.username:20} | Password: farmer{farmers_list.index(farmer)+1:04d} | Name: {farmer.full_name}")
        print(f"... and 95 more farmers (see FARMERS_LIST.txt)")
        
        # Save all farmer credentials to file
        with open('FARMERS_LIST.txt', 'w') as f:
            f.write("="*80 + "\n")
            f.write("KENYA COFFEE FACTORY MANAGEMENT SYSTEM\n")
            f.write("COMPLETE FARMER CREDENTIALS LIST\n")
            f.write("="*80 + "\n\n")
            f.write(f"{'No.':<5} {'Username':<25} {'Password':<15} {'Full Name':<30} {'Member No.':<12} {'Phone':<15}\n")
            f.write("-"*102 + "\n")
            
            for idx, farmer in enumerate(farmers_list, 1):
                f.write(f"{idx:<5} {farmer.username:<25} farmer{idx:<11} {farmer.full_name:<30} {farmer.membership_number:<12} {farmer.phone:<15}\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write(f"Total Farmers: {len(farmers_list)}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("\n📄 Complete farmer list saved to FARMERS_LIST.txt")
        print("\n🎉 Database population complete!")

if __name__ == '__main__':
    populate_farmers_and_deliveries()
