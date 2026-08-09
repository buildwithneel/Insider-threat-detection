import os
import json
import sys
from datetime import datetime
from pymongo import MongoClient

def parse_date_robust(val):
    """
    Robustly parses string timestamps of various ISO and SQL formats into datetime objects.
    """
    if isinstance(val, datetime):
        return val
    if not isinstance(val, str):
        return val
    
    val = val.strip()
    # Try standard SQL/CSV format first
    for fmt in [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d"
    ]:
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            pass
            
    # Try ISO fromisoformat fallback
    try:
        # In Python 3.11+, handles space separator; in older versions, may raise ValueError
        return datetime.fromisoformat(val)
    except ValueError:
        return val


from pymongo.errors import DuplicateKeyError

class MockCollection:
    def __init__(self, filename):
        self.filepath = os.path.join("backend", "mock_db", filename)
        self._unique_fields = set()
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                json.dump([], f)
        self._cache = None

    def _read_data(self):
        if self._cache is not None:
            return self._cache
        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
                # Convert date strings back to datetime objects
                for doc in data:
                    if "timestamp" in doc:
                        doc["timestamp"] = parse_date_robust(doc["timestamp"])
                    if "created_at" in doc:
                        doc["created_at"] = parse_date_robust(doc["created_at"])
                    if "last_login" in doc:
                        doc["last_login"] = parse_date_robust(doc["last_login"])
                self._cache = data
                return data
        except Exception:
            return []

    def _write_data(self, data):
        self._cache = data
        def make_serializable(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [make_serializable(i) for i in obj]
            return obj

        serializable_data = []
        for doc in data:
            new_doc = doc.copy()
            if "_id" in new_doc:
                new_doc["_id"] = str(new_doc["_id"])
            for key, val in new_doc.items():
                new_doc[key] = make_serializable(val)
            serializable_data.append(new_doc)
            
        with open(self.filepath, "w") as f:
            json.dump(serializable_data, f, indent=2)

    def _match_query(self, doc, query):
        if not query:
            return True
        for key, val in query.items():
            if key == "event_id" and isinstance(val, dict) and "$regex" in val:
                regex = val["$regex"].replace("^", "")
                if not str(doc.get("event_id", "")).startswith(regex):
                    return False
                continue
            if key == "alert_id" and isinstance(val, dict) and "$regex" in val:
                regex = val["$regex"].replace("^", "")
                if not str(doc.get("alert_id", "")).startswith(regex):
                    return False
                continue
            if key == "current_score" and isinstance(val, dict) and "$lt" in val:
                if doc.get("current_score", 100) >= val["$lt"]:
                    return False
                continue
            if doc.get(key) != val:
                return False
        return True

    def find_one(self, query=None, projection=None):
        data = self._read_data()
        for doc in data:
            if self._match_query(doc, query):
                return doc
        return None

    def find(self, query=None, projection=None):
        data = self._read_data()
        matches = [doc for doc in data if self._match_query(doc, query)]
        
        class MockCursor(list):
            def sort(self, key_or_list, direction=1):
                if isinstance(key_or_list, list):
                    key = key_or_list[0][0]
                    rev = key_or_list[0][1] == -1
                else:
                    key = key_or_list
                    rev = direction == -1
                
                def get_sort_val(x):
                    val = x.get(key)
                    if val is None:
                        return datetime.min
                    if isinstance(val, str):
                        parsed = parse_date_robust(val)
                        if isinstance(parsed, datetime):
                            return parsed
                        return datetime.min
                    return val
                
                super().sort(key=get_sort_val, reverse=rev)
                return self

            def limit(self, count):
                if count is None or count <= 0:
                    return self
                return MockCursor(self[:count])
        
        return MockCursor(matches)

    def count_documents(self, query=None):
        return len(self.find(query))

    def insert_one(self, doc):
        data = self._read_data()
        # Enforce unique index rules if defined
        for field in getattr(self, "_unique_fields", set()):
            if field in doc and doc[field] is not None:
                val = doc[field]
                for existing in data:
                    if existing.get(field) == val:
                        raise DuplicateKeyError(f"E11000 duplicate key error collection: index: {field}_1 dup key: {{ {field}: \"{val}\" }}")
        
        if "_id" not in doc:
            from bson import ObjectId
            doc["_id"] = ObjectId()
        data.append(doc)
        self._write_data(data)
        
        class MockInsertOneResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return MockInsertOneResult(doc["_id"])

    def insert_many(self, docs):
        data = self._read_data()
        for doc in docs:
            if "_id" not in doc:
                from bson import ObjectId
                doc["_id"] = ObjectId()
            data.append(doc)
        self._write_data(data)
        return docs

    def update_one(self, query, update, upsert=False):
        data = self._read_data()
        found = False
        
        set_fields = update.get("$set", {})
        inc_fields = update.get("$inc", {})
        setOnInsert = update.get("$setOnInsert", {})
        
        target_doc = None
        for doc in data:
            if self._match_query(doc, query):
                target_doc = doc
                found = True
                break

        if found and target_doc is not None:
            for k, v in set_fields.items():
                if k.startswith("details."):
                    subkey = k.split(".")[1]
                    if "details" not in target_doc:
                        target_doc["details"] = {}
                    target_doc["details"][subkey] = v
                else:
                    target_doc[k] = v
            for k, v in inc_fields.items():
                target_doc[k] = target_doc.get(k, 0) + v
        elif not found and upsert:
            new_doc = query.copy()
            for k, v in set_fields.items():
                if k.startswith("details."):
                    subkey = k.split(".")[1]
                    if "details" not in new_doc:
                        new_doc["details"] = {}
                    new_doc["details"][subkey] = v
                else:
                    new_doc[k] = v
            for k, v in inc_fields.items():
                new_doc[k] = v
            for k, v in setOnInsert.items():
                new_doc[k] = v
            data.append(new_doc)
            
        self._write_data(data)
        
        class MockUpdateResult:
            def __init__(self, matched, modified):
                self.matched_count = matched
                self.modified_count = modified
        return MockUpdateResult(1 if found else (1 if upsert else 0), 1 if found or upsert else 0)

    def update_many(self, query, update):
        data = self._read_data()
        set_fields = update.get("$set", {})
        count = 0
        for doc in data:
            if self._match_query(doc, query):
                for k, v in set_fields.items():
                    doc[k] = v
                count += 1
        if count > 0:
            self._write_data(data)
        return count

    def delete_many(self, query):
        data = self._read_data()
        original_len = len(data)
        data = [doc for doc in data if not self._match_query(doc, query)]
        if len(data) != original_len:
            self._write_data(data)
        return original_len - len(data)

    def create_index(self, keys, **kwargs):
        if kwargs.get("unique"):
            if not hasattr(self, "_unique_fields"):
                self._unique_fields = set()
            if isinstance(keys, list):
                for k in keys:
                    field = k[0] if isinstance(k, tuple) else k
                    self._unique_fields.add(field)
            elif isinstance(keys, str):
                self._unique_fields.add(keys)
        return "index_created"

    def bulk_write(self, operations):
        data = self._read_data()
        
        primary_key = None
        if operations:
            first_q = operations[0]._filter
            if len(first_q) == 1:
                key = list(first_q.keys())[0]
                if key in ["event_id", "employee_id", "alert_id"]:
                    primary_key = key
                    
        lookup = {}
        if primary_key:
            for doc in data:
                val = doc.get(primary_key)
                if val:
                    lookup[val] = doc
                    
        for op in operations:
            query = op._filter
            update = op._doc
            upsert = op._upsert
            
            found = False
            set_fields = update.get("$set", {})
            setOnInsert = update.get("$setOnInsert", {})
            
            if primary_key and primary_key in query:
                val = query[primary_key]
                doc = lookup.get(val)
                if doc:
                    for k, v in set_fields.items():
                        if k.startswith("details."):
                            subkey = k.split(".")[1]
                            if "details" not in doc:
                                doc["details"] = {}
                            doc["details"][subkey] = v
                        else:
                            doc[k] = v
                    found = True
            else:
                for doc in data:
                    if self._match_query(doc, query):
                        for k, v in set_fields.items():
                            if k.startswith("details."):
                                subkey = k.split(".")[1]
                                if "details" not in doc:
                                    doc["details"] = {}
                                doc["details"][subkey] = v
                            else:
                                doc[k] = v
                        found = True
                        break
                        
            if not found and upsert:
                new_doc = query.copy()
                for k, v in set_fields.items():
                    if k.startswith("details."):
                        subkey = k.split(".")[1]
                        if "details" not in new_doc:
                            new_doc["details"] = {}
                        new_doc["details"][subkey] = v
                    else:
                        new_doc[k] = v
                for k, v in setOnInsert.items():
                    new_doc[k] = v
                data.append(new_doc)
                if primary_key and primary_key in query:
                    lookup[query[primary_key]] = new_doc
                    
        self._write_data(data)


class MockDatabase:
    def __init__(self):
        self.employees = MockCollection("employees.json")
        self.events = MockCollection("events.json")
        self.trust_scores = MockCollection("trust_scores.json")
        self.alerts = MockCollection("alerts.json")
        self.simulations = MockCollection("simulations.json")
        self.users = MockCollection("users.json")
        self._collections = {
            "employees": self.employees,
            "events": self.events,
            "trust_scores": self.trust_scores,
            "alerts": self.alerts,
            "simulations": self.simulations,
            "users": self.users,
        }

    def get_database(self):
        return self

    def __getitem__(self, item):
        if item not in self._collections:
            self._collections[item] = MockCollection(f"{item}.json")
            setattr(self, item, self._collections[item])
        return self._collections[item]

    def __getattr__(self, name):
        if name in self._collections:
            return self._collections[name]
        coll = MockCollection(f"{name}.json")
        self._collections[name] = coll
        setattr(self, name, coll)
        return coll


_mock_db_instance = None

def get_db(mongodb_uri=None):
    global _mock_db_instance
    if not mongodb_uri:
        mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/garudaai")
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        if k.strip() == "MONGODB_URI":
                            mongodb_uri = v.strip().strip('"').strip("'")
                            
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=1000)
        client.server_info()
        print(f"Database Connected: Actual MongoDB Server ({mongodb_uri})")
        return client.get_database()
    except Exception:
        print("Database Connected: Fallback File-Based JSON Database (Active)")
        if _mock_db_instance is None:
            _mock_db_instance = MockDatabase()
        return _mock_db_instance

