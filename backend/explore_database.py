import mysql.connector

# Database connection
def connect_database():
    return mysql.connector.connect(
        host='92.113.22.65',
        user='u906714182_sqlrrefdvdv',
        password='3@6*t:lU',
        database='u906714182_sqlrrefdvdv'
    )

def explore_tables():
    """Explore table structure to understand the setup"""
    try:
        conn = connect_database()
        cursor = conn.cursor(dictionary=True)
        
        # Show all tables
        print("📋 Available Tables:")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            print(f"   {table}")
            
        # Check tblstaff structure
        print("\n🏗️ tblstaff Table Structure:")
        try:
            cursor.execute("DESCRIBE tblstaff")
            structure = cursor.fetchall()
            for field in structure:
                print(f"   {field}")
        except Exception as e:
            print(f"   Error with tblstaff: {e}")
            
        # Check tblchatmessages structure
        print("\n💬 tblchatmessages Table Structure:")
        try:
            cursor.execute("DESCRIBE tblchatmessages")
            structure = cursor.fetchall()
            for field in structure:
                print(f"   {field}")
        except Exception as e:
            print(f"   Error with tblchatmessages: {e}")
            
        # Try to find AI agent with different approach
        print("\n🔍 Looking for AI Agent...")
        try:
            cursor.execute("SELECT * FROM tblstaff LIMIT 5")
            sample_staff = cursor.fetchall()
            print("Sample staff records:")
            for staff in sample_staff:
                print(f"   {staff}")
        except Exception as e:
            print(f"   Error querying tblstaff: {e}")
            
        # Check for COORDINATION AGENT
        try:
            cursor.execute("SELECT * FROM tblstaff WHERE staffname LIKE '%COORDINATION%' OR staffname LIKE '%AI%'")
            ai_staff = cursor.fetchall()
            if ai_staff:
                print(f"\n🤖 Found AI Agent:")
                for agent in ai_staff:
                    print(f"   {agent}")
            else:
                print("\n❌ No AI agent found with COORDINATION or AI in name")
        except Exception as e:
            print(f"   Error searching for AI agent: {e}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error exploring tables: {str(e)}")

if __name__ == "__main__":
    explore_tables()