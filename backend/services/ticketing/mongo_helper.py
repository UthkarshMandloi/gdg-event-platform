from pymongo import MongoClient

class MongoDBClient:
    def __init__(self, config):
        try:
            self.client = MongoClient(config.mongo_uri)
            self.db = self.client[config.mongo_db_name]
            self.collection = self.db[config.mongo_collection_name]
            print("[MongoDB] Connection successful.")
        except Exception as e:
            print(f"[MongoDB] ERROR: Could not connect: {e}")
            raise Exception(f"MongoDB Connection Failed: {e}")

    def insert_full_attendee(self, attendee_data):
        """Inserts the complete dictionary into MongoDB"""
        self.collection.insert_one(attendee_data)
        print(f"[MongoDB] Inserted new attendee: {attendee_data.get('Name')} ({attendee_data.get('Attendee ID')})")

    def find_attendee_by_email_and_name(self, email, name):
        """Finds attendee by their Email ID"""
        # We search using 'Email ID' because that's the default column name we assigned!
        return self.collection.find_one({"Email ID": email})

    def update_attendee_field(self, attendee_id, field_name, value):
        """Updates a specific field for an attendee"""
        
        # CRITICAL FIX: We must search for "Attendee ID" exactly as it is saved in the dict!
        result = self.collection.update_one(
            {"Attendee ID": attendee_id},
            {"$set": {field_name: value}}
        )
        
        if result.modified_count > 0:
            print(f"[MongoDB] Updated {field_name} for ID {attendee_id}")
        else:
            print(f"[MongoDB] Warning: Could not find/update Attendee ID: {attendee_id}")