import psycopg
import subprocess
import os
import argparse
from typing import List, Tuple
from dotenv import load_dotenv

class PostgresToSQLServerMigrator:
    def __init__(
            self, 
            pg_host: str, 
            pg_database: str, 
            pg_user: str, 
            pg_password: str,
            sqlserver_server: str, 
            sqlserver_database: str, 
            sqlserver_user: str, 
            sqlserver_password: str,
            pg_port: int = 5432
    ):
        
        self.pg_config = {
            'host': pg_host,
            'dbname': pg_database,
            'user': pg_user,
            'password': pg_password,
            'port': pg_port
        }
        
        self.sqlserver_config = {
            'server': sqlserver_server,
            'database': sqlserver_database,
            'user': sqlserver_user,
            'password': sqlserver_password
        }
        self.batch_size = 999
    
    def fetch_data_from_postgres(self, query: str) -> Tuple[List[Tuple], List[str]]:
        try:
            conn = psycopg.connect(**self.pg_config)
            cursor = conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            cursor.close()
            conn.close()
            return data, columns
        except Exception as e:
            print(f"Errore durante il fetch da PostgreSQL: {e}")
            raise
    
    def generate_insert_statements(
            self,
            data: List[Tuple],
            columns: List[str],
            target_table: str
    ) -> str:
        if not data:
            return ""
        
        columns_str = ', '.join(columns)
        insert_statements = []
        
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            values_list = []
            for row in batch:
                formatted_values = []
                for value in row:
                    if value is None:
                        formatted_values.append('NULL')
                    elif isinstance(value, str):
                        escaped_value = value.replace("'", "''")
                        formatted_values.append(f"'{escaped_value}'")
                    elif isinstance(value, (int, float)):
                        formatted_values.append(str(value))
                    else:
                        formatted_values.append(f"'{str(value)}'")
                
                values_list.append(f"({', '.join(formatted_values)})")
            
            insert_sql = f"INSERT INTO {target_table} ({columns_str}) VALUES\n"
            insert_sql += ',\n'.join(values_list) + ';\nGO\n\n'
            insert_statements.append(insert_sql)
        
        return ''.join(insert_statements)
    
    def save_script_to_file(self, sql_script: str, filename: str = 'migration_script.sql') -> str:
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sql_script)
        print(f"Script salvato in: {filepath}")
        return filepath
    
    @staticmethod
    def load_query_from_file(filename: str) -> str:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    
    def execute_with_sqlcmd(self, script_file: str):
        try:
            windows_path = script_file
            #check WSL environment and convert path if necessary
            if os.path.exists('/proc/version'):
                result_path = subprocess.run(
                    ['wslpath', '-w', script_file], 
                    capture_output=True, 
                    text=True
                )
                if result_path.returncode == 0:
                    windows_path = result_path.stdout.strip()
            
            cmd = [
                'sqlcmd.exe',
                '-S', self.sqlserver_config['server'],
                '-d', self.sqlserver_config['database'],
                '-U', self.sqlserver_config['user'],
                '-P', self.sqlserver_config['password'],
                '-i', windows_path
            ]
            
            print(f"Esecuzione sqlcmd.exe...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Script eseguito con successo!")
                print(result.stdout)
            else:
                print(f"Errore durante l'esecuzione: {result.stderr}")
                raise Exception(result.stderr)
                
        except Exception as e:
            print(f"Errore durante l'esecuzione di sqlcmd: {e}")
            raise
    
    def migrate(
            self, 
            postgres_query: str, 
            target_table: str,
            output_filename: str = 'migration_script.sql',
            execute: bool = True
        ) -> str:
        print("1. Recupero dati da PostgreSQL...")
        data, columns = self.fetch_data_from_postgres(postgres_query)
        print(f"   Recuperate {len(data)} righe")
        
        print("2. Generazione INSERT statements...")
        sql_script = self.generate_insert_statements(data, columns, target_table)
        
        print("3. Salvataggio script su file...")
        script_file = self.save_script_to_file(sql_script, output_filename)
        
        if execute:
            print("4. Esecuzione script su SQL Server...")
            self.execute_with_sqlcmd(script_file)
        else:
            print("4. Script generato ma non eseguito (execute=False)")
        
        return script_file
    
    def migrate_multiple_periods(
            self,
            query_template: str,
            target_table: str, 
            reference_periods: List[str], 
            execute: bool = True
        ) -> List[str]:
        generated_files = []
        
        for period in reference_periods:
            print(f"\n{'='*60}")
            print(f"Elaborazione periodo: {period}")
            print(f"{'='*60}")
            
            query = query_template.replace('{reference_period}', period)
            output_filename = f'tb_spend_l2_{period}.sql'
            script_file = self.migrate(
                postgres_query=query,
                target_table=target_table,
                output_filename=output_filename,
                execute=execute
            )
            generated_files.append(script_file)
        
        print(f"\n{'='*60}")
        print(f"Completato! Generati {len(generated_files)} file")
        print(f"{'='*60}")
        return generated_files


if __name__ == "__main__":
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Migrazione dati da PostgreSQL a SQL Server')
    parser.add_argument('-g', '--generate-only', action='store_true',
                        help='Genera solo gli script SQL senza eseguirli')
    args = parser.parse_args()
    
    migrator = PostgresToSQLServerMigrator(
        pg_host=os.getenv('POSTGRES_HOST'),
        pg_database=os.getenv('POSTGRES_DATABASE'),
        pg_user=os.getenv('POSTGRES_USER'),
        pg_password=os.getenv('POSTGRES_PASSWORD'),
        sqlserver_server=os.getenv('SQLSERVER_HOST'),
        sqlserver_database=os.getenv('SQLSERVER_DATABASE'),
        sqlserver_user=os.getenv('SQLSERVER_USER'),
        sqlserver_password=os.getenv('SQLSERVER_PASSWORD'),
        pg_port=int(os.getenv('POSTGRES_PORT', 5432))
    )
    
    query_template = PostgresToSQLServerMigrator.load_query_from_file('extraction_query.sql')
    reference_periods = ['2025Q1', '2025Q2', '2025Q3', '2025Q4']
    execute = not args.generate_only
    if args.generate_only:
        print("Modalità: Solo generazione script (senza esecuzione)")
    else:
        print("Modalità: Generazione ed esecuzione migrazione")
    
    migrator.migrate_multiple_periods(
        query_template=query_template,
        target_table=os.getenv('TARGET_TABLE'),
        reference_periods=reference_periods,
        execute=execute
    )