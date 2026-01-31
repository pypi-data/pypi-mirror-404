from pymongo import MongoClient

class Operating_MongoDB:
    def __init__(self, uri='mongodb://localhost:27017', db_name='myDatabase'):
        """初始化 MongoDB 客户端，连接到指定的数据库"""
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None

    def connect(self):
        """连接到 MongoDB 数据库"""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def get_collection(self, collection_name):
        """获取指定名称的集合"""
        if self.db is None:
            raise Exception("Database connection not established. Call connect() first.")
        return self.db[collection_name]

    def insert_one(self, collection_name, document):
        """向指定集合插入单个文档"""
        collection = self.get_collection(collection_name)
        result = collection.insert_one(document)
        print(f"Inserted document with _id: {result.inserted_id}")
        return result.inserted_id

    def insert_many(self, collection_name, documents):
        """向指定集合插入多个文档"""
        collection = self.get_collection(collection_name)
        result = collection.insert_many(documents)
        print(f"Inserted {len(result.inserted_ids)} documents")
        return result.inserted_ids

    def find_one(self, collection_name, query):
        """根据查询条件查询单个文档"""
        collection = self.get_collection(collection_name)
        document = collection.find_one(query)
        return document

    def find(self, collection_name, query):
        """根据查询条件查询所有匹配的文档"""
        collection = self.get_collection(collection_name)
        documents = collection.find(query)
        return list(documents)

    def find_all(self, collection_name):
        """根据查询条件查询所有匹配的文档"""
        collection = self.get_collection(collection_name)
        documents = collection.find()
        return list(documents)

    def update_one(self, collection_name, filter_query, update_query):
        """更新一个匹配的文档"""
        collection = self.get_collection(collection_name)
        result = collection.update_one(filter_query, update_query)
        print(f"Matched {result.matched_count} document(s) and modified {result.modified_count} document(s)")
        return result

    def update_many(self, collection_name, filter_query, update_query):
        """更新多个匹配的文档"""
        collection = self.get_collection(collection_name)
        result = collection.update_many(filter_query, update_query)
        print(f"Matched {result.matched_count} document(s) and modified {result.modified_count} document(s)")
        return result

    def delete_one(self, collection_name, query):
        """删除一个匹配的文档"""
        collection = self.get_collection(collection_name)
        result = collection.delete_one(query)
        print(f"Deleted {result.deleted_count} document(s)")
        return result

    def delete_many(self, collection_name, query):
        """删除多个匹配的文档"""
        collection = self.get_collection(collection_name)
        result = collection.delete_many(query)
        print(f"Deleted {result.deleted_count} document(s)")
        return result

    def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
        else:
            print("No active connection to close.")


# 使用示例
if __name__ == "__main__":
    # 连接 MongoDB
    mongo_client = Operating_MongoDB()
    mongo_client.connect()

    # 插入单个文档
    mongo_client.insert_one('myCollection', {"name": "Alice", "age": 30})

    # 插入多个文档
    mongo_client.insert_many('myCollection', [
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
        {"name": "David", "age": 30}
    ])

    # 查询单个文档
    person = mongo_client.find_one('myCollection', {"name": "Alice"})
    print(f"Found person: {person}")

    # 查询多个文档
    people = mongo_client.find('myCollection', {"age": {"$gte": 30}})
    print(f"People older than 30: {people}")

    # 查询所有文档
    people = mongo_client.find_all('myCollection')
    print(f"People older than 30: {people}")

    # 更新单个文档
    mongo_client.update_one('myCollection', {"name": "Alice"}, {"$set": {"age": 31}})

    # 更新多个文档（年龄大于等于 30 的人都更新他们的状态为 'senior'）
    mongo_client.update_many('myCollection', {"age": {"$gte": 30}}, {"$set": {"status": "senior"}})

    # 查询更新后的文档
    updated_people = mongo_client.find_all('myCollection')
    print(f"Updated people: {updated_people}")

   # 删除一个文档
    mongo_client.delete_one('myCollection', {"name": "Bob"})

    # 删除多个文档（删除年龄小于 30 的人）
    mongo_client.delete_many('myCollection', {"age": {"$lt": 30}})

    # 关闭连接
    mongo_client.close()
