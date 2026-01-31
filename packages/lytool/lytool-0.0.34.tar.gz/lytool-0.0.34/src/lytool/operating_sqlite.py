import sqlite3
from contextlib import contextmanager
import os

class Operating_SQLite:
    def __init__(self, db_file=r'C:\Users\admin\AppData\Roaming\comfyDesk\identifier.sqlite', auto_connect=False):
        """
        初始化SQLite数据库操作类

        Args:
            db_file (str): 数据库文件路径
            auto_connect (bool, optional): 是否自动管理连接. 默认为True.
                True: 初始化时连接，显式调用close()或程序结束时断开
                False: 执行SQL时连接，执行完毕后立即断开
        """
        self.db_file = db_file
        self.connection = None
        self.auto_connect = auto_connect
        self._validate_db_path()
        # 如果启用自动连接，立即连接数据库
        if auto_connect:
            self._connect()

    def _validate_db_path(self):
        """验证数据库路径合法性并确保目录存在"""
        db_dir = os.path.dirname(self.db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _connect(self):
        """建立数据库连接（内部使用）"""
        if not self.connection:
            self.connection = sqlite3.connect(self.db_file)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def _disconnect(self):
        """断开数据库连接（内部使用）"""
        if self.connection:
            self.connection.close()
            self.connection = None

    @contextmanager
    def _managed_cursor(self):
        """
        管理游标生命周期的上下文管理器
        根据auto_connect参数决定是否自动连接/断开
        """
        should_disconnect = False
        try:
            # 确保在需要时建立连接
            if self.connection is None:
                self._connect()
                # 只有在auto_connect=False模式下才在操作后断开
                should_disconnect = not self.auto_connect

            cursor = self.connection.cursor()
            yield cursor
            self.connection.commit()
        except Exception as e:
            # 只有在连接有效时才回滚
            if self.connection is not None:
                self.connection.rollback()
            raise e
        finally:
            # 只有在auto_connect=False模式下才在操作后断开
            if should_disconnect and self.connection is not None:
                self._disconnect()

    def create_table(self, table_name, columns):
        """
        创建数据库表

        Args:
            table_name (str): 表名
            columns (dict): 列定义字典，格式: {'column1': 'INTEGER PRIMARY KEY', 'column2': 'TEXT NOT NULL'}

        Example:
            db.create_table('users', {
                'id': 'INTEGER PRIMARY KEY',
                'name': 'TEXT NOT NULL',
                'age': 'INTEGER'
            })
        """
        column_defs = ', '.join([f'{name} {definition}' for name, definition in columns.items()])
        sql = f'CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})'
        with self._managed_cursor() as cursor:
            cursor.execute(sql)

    def insert(self, table_name, data):
        """
        插入单条数据

        Args:
            table_name (str): 表名
            data (dict): 数据字典，格式: {'column1': value1, 'column2': value2}

        Returns:
            int: 插入行的ID

        Example:
            db.insert('users', {'name': 'Alice', 'age': 30})
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())
        sql = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
        with self._managed_cursor() as cursor:
            cursor.execute(sql, values)
            return cursor.lastrowid

    def select(self, table_name, columns='*', where=None, order_by=None, limit=None, offset=None, as_dict=True):
        """
        查询数据

        Args:
            table_name (str): 表名
            columns (str, optional): 要查询的列，默认'*'
            where (dict|list, optional): 查询条件
                字典格式: {'column1': value1, 'column2': value2} 表示 AND 关系的等值查询
                列表格式: [('column1', '>', value1), ('column2', 'LIKE', '%text%')] 支持多种运算符
            order_by (str, optional): 排序字段
            limit (int, optional): 返回记录数限制
            offset (int, optional): 偏移量
            as_dict (bool, optional): 是否以字典形式返回结果，默认为True

        Returns:
            list: 查询结果列表，元素类型根据as_dict参数决定

        Example:
            # 等值查询，返回字典列表
            users = db.select('users', where={'age': 25})

            # 复杂条件查询，返回原始Row对象
            rows = db.select('users',
                           where=[('age', '>', 25), ('status', 'IN', ('active', 'pending'))],
                           order_by='age DESC',
                           as_dict=False)
        """
        sql = f'SELECT {columns} FROM {table_name}'
        values = []
        if where:
            if isinstance(where, dict):
                # 字典格式处理等值条件
                conditions = [f'{k} = ?' for k in where]
                values = tuple(where.values())
                sql += ' WHERE ' + ' AND '.join(conditions)
            elif isinstance(where, list):
                # 列表格式处理复杂条件
                conditions = []
                for item in where:
                    if len(item) == 3:
                        col, op, val = item
                        if op.upper() == 'IN':
                            # 处理IN操作符
                            placeholders = ', '.join(['?'] * len(val))
                            conditions.append(f"{col} IN ({placeholders})")
                            values.extend(val)
                        else:
                            conditions.append(f"{col} {op} ?")
                            values.append(val)
                sql += ' WHERE ' + ' AND '.join(conditions)
        if order_by:
            sql += f' ORDER BY {order_by}'
        if limit:
            sql += f' LIMIT {limit}'
        if offset:
            sql += f' OFFSET {offset}'
        with self._managed_cursor() as cursor:
            cursor.execute(sql, values)
            rows = cursor.fetchall()

            if as_dict:
                # 将sqlite3.Row对象转换为字典
                return [dict(row) for row in rows]
            else:
                return rows

    def update(self, table_name, data, where):
        """
        更新数据

        Args:
            table_name (str): 表名
            data (dict): 要更新的数据，格式: {'column1': new_value1, 'column2': new_value2}
            where (dict|list): 更新条件，格式同select方法的where参数

        Returns:
            int: 受影响的行数

        Example:
            # 等值条件更新
            db.update('users', {'age': 30}, {'id': 1})

            # 复杂条件更新
            db.update('users', {'status': 'inactive'}, [
                ('last_login', '<', '2023-01-01'),
                ('is_active', '=', False)
            ])
        """
        set_clause = ', '.join([f'{k} = ?' for k in data])
        values = list(data.values())
        where_clause, where_values = self._parse_where(where)
        values.extend(where_values)
        sql = f'UPDATE {table_name} SET {set_clause} WHERE {where_clause}'
        with self._managed_cursor() as cursor:
            cursor.execute(sql, values)
            return cursor.rowcount

    def delete(self, table_name, where):
        """
        删除数据

        Args:
            table_name (str): 表名
            where (dict|list): 删除条件，格式同select方法的where参数

        Returns:
            int: 受影响的行数

        Example:
            # 等值条件删除
            db.delete('users', {'id': 1})

            # 复杂条件删除
            db.delete('users', [('age', '>', 100), ('is_active', '=', False)])
        """
        where_clause, where_values = self._parse_where(where)
        sql = f'DELETE FROM {table_name} WHERE {where_clause}'
        with self._managed_cursor() as cursor:
            cursor.execute(sql, where_values)
            return cursor.rowcount

    def _parse_where(self, where):
        """解析where条件（内部使用）"""
        conditions = []
        values = []
        if isinstance(where, dict):
            conditions = [f'{k} = ?' for k in where]
            values = list(where.values())
        elif isinstance(where, list):
            for item in where:
                if len(item) == 3:
                    col, op, val = item
                    if op.upper() == 'IN':
                        placeholders = ', '.join(['?'] * len(val))
                        conditions.append(f"{col} IN ({placeholders})")
                        values.extend(val)
                    else:
                        conditions.append(f"{col} {op} ?")
                        values.append(val)
        return ' AND '.join(conditions), values

    def execute(self, sql, parameters=None):
        """
        执行自定义SQL语句

        Args:
            sql (str): SQL语句
            parameters (tuple, optional): 参数元组

        Returns:
            list: SELECT语句返回查询结果
            int: 其他语句返回受影响的行数

        Example:
            # 执行自定义查询
            result = db.execute('SELECT * FROM users WHERE age > ?', (25,))

            # 执行自定义更新
            count = db.execute('UPDATE users SET age = age + 1')
        """
        with self._managed_cursor() as cursor:
            cursor.execute(sql, parameters or ())
            if sql.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                return cursor.rowcount

    def close(self):
        """显式关闭数据库连接"""
        self._disconnect()

if __name__ == '__main__':
    mySQLite = Operating_SQLite()
    mySQLite.insert('parameterManage', {'parameterId':'2235', 'imageVideoPate':'e:/a.webp', 'parameter':'{"a":"b"}'})
    mySQLite.delete('parameterManage', {'parameterId':'2234'})
    mySQLite.update('parameterManage', {'imageVideoPate':'d:/a.webp'}, {'parameterId': '2235'})
    print('parameterManage:', mySQLite.select('parameterManage'))
