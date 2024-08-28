def get_distinct_project_names():
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT project_name FROM cost_dist")
        results = cursor.fetchall()
    return [row[0] for row in results if row[0]]  # Extract project names and filter out None values