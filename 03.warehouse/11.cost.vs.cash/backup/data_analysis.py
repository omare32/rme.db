import mysql.connector as mysql
import pandas as pd
import matplotlib.pyplot as plt
import os

def fetch_data(cursor, query, columns):
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=columns)
    df['AMOUNT'] = pd.to_numeric(df['AMOUNT'], errors='coerce')
    return df

def create_bar_plot(data, title, output_path, ylabel):
    plt.figure(figsize=(15, 8))
    plt.barh(range(len(data)), data.values/1_000_000)
    plt.title(title)
    plt.xlabel('Amount (Millions EGP)')
    plt.ylabel(ylabel)
    plt.yticks(range(len(data)), data.index)
    
    # Add value labels
    for i, v in enumerate(data.values):
        plt.text(v/1_000_000, i, f'{v/1_000_000:,.1f}M', va='center')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_comparison_plot(cost_data, cash_data, title, output_path, ylabel):
    plt.figure(figsize=(15, 10))
    
    # Get all unique indices
    all_indices = sorted(set(cost_data.index) | set(cash_data.index))
    
    # Prepare data
    cost_values = [cost_data.get(idx, 0)/1_000_000 for idx in all_indices]
    cash_values = [cash_data.get(idx, 0)/1_000_000 for idx in all_indices]
    
    # Create bars
    y_pos = range(len(all_indices))
    plt.barh([y - 0.2 for y in y_pos], cost_values, 0.4, label='Cost', color='#ff7f0e')
    plt.barh([y + 0.2 for y in y_pos], cash_values, 0.4, label='Cash', color='#1f77b4')
    
    plt.title(title)
    plt.xlabel('Amount (Millions EGP)')
    plt.ylabel(ylabel)
    plt.yticks(y_pos, all_indices)
    plt.legend()
    
    # Add value labels
    for i, (cost_v, cash_v) in enumerate(zip(cost_values, cash_values)):
        if cost_v > 0:
            plt.text(cost_v, i - 0.2, f'{cost_v:,.1f}M', va='center')
        if cash_v > 0:
            plt.text(cash_v, i + 0.2, f'{cash_v:,.1f}M', va='center')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # Create output directory if it doesn't exist
    output_dir = '03.warehouse/11.cost.vs.cash'
    os.makedirs(output_dir, exist_ok=True)

    # Connection details
    host = "10.10.11.242"
    user = "omar2"
    password = "Omar_54321"
    database = "RME_TEST"

    try:
        print("Connecting to database...")
        connection = mysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        
        if connection.is_connected():
            print("Connected to MySQL database")

        cursor = connection.cursor()

        # Fetch cost data
        print("Fetching cost data...")
        cost_query = """
        SELECT 
            PROJECT_NAME,
            VENDOR_NAME,
            AMOUNT,
            GL_DATE
        FROM RME_Projects_Cost_Dist_Line_Report
        WHERE GL_DATE LIKE '2025%'
        AND TRANSACTION_SOURCE != 'Inventory Misc'
        """
        cost_df = fetch_data(cursor, cost_query, ['PROJECT_NAME', 'VENDOR_NAME', 'AMOUNT', 'GL_DATE'])
        print(f"Fetched {len(cost_df)} cost records")

        # Fetch cash data
        print("Fetching cash data...")
        cash_query = """
        SELECT 
            PROJECT_NAME,
            `Supplier Name` as VENDOR_NAME,
            AMOUNT,
            CHECK_DATE
        FROM RME_ap_check_payments_Report
        WHERE YEAR(CHECK_DATE) = 2025
        """
        cash_df = fetch_data(cursor, cash_query, ['PROJECT_NAME', 'VENDOR_NAME', 'AMOUNT', 'CHECK_DATE'])
        print(f"Fetched {len(cash_df)} cash records")

        # Calculate totals
        cost_project_totals = cost_df.groupby('PROJECT_NAME')['AMOUNT'].sum().sort_values(ascending=True)
        cost_vendor_totals = cost_df.groupby('VENDOR_NAME')['AMOUNT'].sum().sort_values(ascending=True)
        cash_project_totals = cash_df.groupby('PROJECT_NAME')['AMOUNT'].sum().sort_values(ascending=True)
        cash_vendor_totals = cash_df.groupby('VENDOR_NAME')['AMOUNT'].sum().sort_values(ascending=True)

        # Get top 10s
        top_10_cost_projects = cost_project_totals.tail(10)
        top_10_cost_vendors = cost_vendor_totals.tail(10)
        top_10_cash_projects = cash_project_totals.tail(10)
        top_10_cash_vendors = cash_vendor_totals.tail(10)

        print("\nCreating visualizations...")
        
        # Create individual plots
        create_bar_plot(
            top_10_cost_projects, 
            'Top 10 Projects by Cost (2025)', 
            os.path.join(output_dir, 'cost_projects_2025.png'),
            'Project Name'
        )
        
        create_bar_plot(
            top_10_cost_vendors, 
            'Top 10 Vendors by Cost (2025)', 
            os.path.join(output_dir, 'cost_vendors_2025.png'),
            'Vendor Name'
        )
        
        create_bar_plot(
            top_10_cash_projects, 
            'Top 10 Projects by Cash (2025)', 
            os.path.join(output_dir, 'cash_projects_2025.png'),
            'Project Name'
        )
        
        create_bar_plot(
            top_10_cash_vendors, 
            'Top 10 Vendors by Cash (2025)', 
            os.path.join(output_dir, 'cash_vendors_2025.png'),
            'Vendor Name'
        )

        # Create comparison plots
        # For projects: combine top 10 from both cost and cash
        top_projects = pd.concat([top_10_cost_projects, top_10_cash_projects])
        top_projects = top_projects.index.unique()
        project_comparison = pd.DataFrame({
            'Cost': cost_project_totals[top_projects],
            'Cash': cash_project_totals[top_projects]
        }).fillna(0)
        
        create_comparison_plot(
            project_comparison['Cost'],
            project_comparison['Cash'],
            'Cost vs Cash by Project (2025)',
            os.path.join(output_dir, 'cost_vs_cash_projects_2025.png'),
            'Project Name'
        )

        # For vendors: combine top 10 from both cost and cash
        top_vendors = pd.concat([top_10_cost_vendors, top_10_cash_vendors])
        top_vendors = top_vendors.index.unique()
        vendor_comparison = pd.DataFrame({
            'Cost': cost_vendor_totals[top_vendors],
            'Cash': cash_vendor_totals[top_vendors]
        }).fillna(0)
        
        create_comparison_plot(
            vendor_comparison['Cost'],
            vendor_comparison['Cash'],
            'Cost vs Cash by Vendor (2025)',
            os.path.join(output_dir, 'cost_vs_cash_vendors_2025.png'),
            'Vendor Name'
        )

        # Print summaries
        print("\nTop 10 Projects by Cost:")
        print(top_10_cost_projects.to_frame().to_string())
        
        print("\nTop 10 Projects by Cash:")
        print(top_10_cash_projects.to_frame().to_string())
        
        print("\nTop 10 Vendors by Cost:")
        print(top_10_cost_vendors.to_frame().to_string())
        
        print("\nTop 10 Vendors by Cash:")
        print(top_10_cash_vendors.to_frame().to_string())

        # Save to Excel
        print("\nSaving detailed data to Excel...")
        
        # Save individual analyses
        with pd.ExcelWriter(os.path.join(output_dir, 'cost_analysis_2025.xlsx')) as writer:
            top_10_cost_projects.to_frame('Amount').to_excel(writer, sheet_name='Top Projects')
            top_10_cost_vendors.to_frame('Amount').to_excel(writer, sheet_name='Top Vendors')
            cost_df.to_excel(writer, sheet_name='All Cost Data', index=False)
            
        with pd.ExcelWriter(os.path.join(output_dir, 'cash_analysis_2025.xlsx')) as writer:
            top_10_cash_projects.to_frame('Amount').to_excel(writer, sheet_name='Top Projects')
            top_10_cash_vendors.to_frame('Amount').to_excel(writer, sheet_name='Top Vendors')
            cash_df.to_excel(writer, sheet_name='All Cash Data', index=False)
            
        # Save comparison analysis
        with pd.ExcelWriter(os.path.join(output_dir, 'cost_vs_cash_analysis_2025.xlsx')) as writer:
            project_comparison.to_excel(writer, sheet_name='Project Comparison')
            vendor_comparison.to_excel(writer, sheet_name='Vendor Comparison')
        
        print(f"Analysis complete! Results saved in: {output_dir}")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nMySQL connection is closed")

if __name__ == "__main__":
    main() 