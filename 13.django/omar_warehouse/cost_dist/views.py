from django.shortcuts import render
from django.db import connection
from .forms import CostDistForm

def cost_dist_report(request):
    if request.method == 'POST':
        form = CostDistForm(request.POST)
        if form.is_valid():
            project_identifier = form.cleaned_data['project_identifier']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            show_details = form.cleaned_data['show_details']

            with connection.cursor() as cursor:
                if project_identifier.isdigit():
                    # Project identifier is a project number
                    query = f"""
                        SELECT 
                            project_no, 
                            project_name, 
                            SUM(amount) AS total_cost
                        FROM 
                            cost_dist
                        WHERE 
                            project_no = %s 
                            {f'AND gl_date BETWEEN %s AND %s' if start_date and end_date else ''} 
                        GROUP BY 
                            project_no, project_name;
                    """
                else:
                    # Project identifier is a project name
                    query = f"""
                        SELECT 
                            project_no, 
                            project_name, 
                            SUM(amount) AS total_cost
                        FROM 
                            cost_dist
                        WHERE 
                            project_name = %s 
                            {f'AND gl_date BETWEEN %s AND %s' if start_date and end_date else ''} 
                        GROUP BY 
                            project_no, project_name;
                    """

                # Adjust params based on whether dates are provided
                if start_date and end_date:
                    params = [project_identifier, start_date, end_date]
                else:
                    params = [project_identifier]

                cursor.execute(query, params)
                results = cursor.fetchall()

            if show_details:
                context = {'results': results}
            else:
                total_amount = sum(row[2] for row in results)  # Assuming 'total_cost' is at index 2
                context = {'total_amount': total_amount}

            return render(request, 'cost_dist/report.html', context)
    else:
        form = CostDistForm()

    return render(request, 'cost_dist/report.html', {'form': form})

def get_distinct_project_names():
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT project_name FROM cost_dist")
        results = cursor.fetchall()
    return [row[0] for row in results if row[0]]  # Extract project names and filter out None values