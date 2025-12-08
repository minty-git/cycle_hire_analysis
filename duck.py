import duckdb
con = duckdb.connect(database='cycle_hire_analysis.duckdb')

preview_data_query = "select * from duckdb_tables()"
# preview_data_query = """
# ATTACH 'cycle_hire_analysis.db' AS db1;
# ATTACH 'cycle_hire_analysis_new.db' AS db2;
# COPY FROM DATABASE db1 TO db2;
# """

print(con.execute(preview_data_query).df())

# print(con.sql("PRAGMA show_tables;").fetchall())
