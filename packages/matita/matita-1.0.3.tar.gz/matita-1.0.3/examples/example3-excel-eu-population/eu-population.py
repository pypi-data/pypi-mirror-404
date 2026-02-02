import os

from matita.office import excel as xl

def generate_report():
    xlFormatCommas = 2
    file_path = os.path.dirname(os.path.abspath(__file__)) + "/tps00001__custom_19561911_linear_2_0.csv"

    xl_app = xl.Application()
    xl_app.visible = True
    
    data_wkb = xl_app.workbooks.Open(file_path, ReadOnly=True, Format=xlFormatCommas)
    data_wks = data_wkb.worksheets(1)
    data_tbl = data_wks.list_objects.add(
        SourceType=xl.xlSrcRange,
        Source=data_wks.usedrange,
        XlListObjectHasHeaders=xl.xlYes,
    )
    countries_clm = data_tbl.list_columns("Geopolitical entity (reporting)")
    population_clm = data_tbl.list_columns("OBS_VALUE")

    eu_countries = sorted(set(countries_clm.data_body_range.value))
    eu_countries = [x[0] for x in eu_countries.copy()]

    years = [x[0] for x in data_tbl.list_columns("TIME_PERIOD").data_body_range.value]
    start_year = int(min(years))
    end_year = int(max(years))
    num_rows = end_year - start_year + 1

    report_wkb = xl_app.workbooks.add()
    first_wks = report_wkb.worksheets(1)
    for country in eu_countries:
        last_wks = report_wkb.worksheets(report_wkb.worksheets.count)
        country_wks = report_wkb.worksheets.add(After=last_wks)

        # Add heading
        country_wks.name = country
        country_wks.cells(2, 2).value = f"Population of {country}"
        country_wks.rows(2).style = "Heading 1"
        country_wks.columns(1).column_width = 3

        # Add table
        country_wks.cells(4, 2).Value = "Year"
        country_wks.cells(4, 3).Value = "Population"
        country_wks.cells(5, 2).Value = start_year
        country_wks.cells(5, 2).data_series(Rowcol=xl.xlColumns, Type=xl.xlLinear, Date=xl.xlDay, Step=1, Stop=end_year)

        data_tbl.data_body_range.auto_filter(Field=countries_clm.Index, Criteria1=country)
        country_wks.cells(5, 3).resize(num_rows).value = population_clm.data_body_range.special_cells(xl.xlCellTypeVisible).value

        country_tbl = country_wks.list_objects.add(
            SourceType=xl.xlSrcRange,
            Source=country_wks.cells(4, 2).current_region,
            XlListObjectHasHeaders=xl.xlYes
        )
        country_tbl.list_columns("Population").data_body_range.number_format = "#,##0"

        shp = country_wks.shapes.add_chart2( 
            XlChartType=xl.xlLineMarkers,
            Left=country_wks.cells(4, 5).left,
            Top=country_wks.cells(4, 5).top,
        )
        c = shp.chart
        c.has_title = False
        chart_series = c.full_series_collection(1)
        chart_series.name = country_wks.cells(4, 2).address()
        chart_series.values  = f"'{country}'!{country_tbl.list_columns("Population").data_body_range.address()}"
        chart_series.x_values = f"'{country}'!{country_tbl.list_columns("Year").data_body_range.address()}"

    first_wks.delete()
    data_wkb.close(False)
    report_wkb.worksheets(1).activate()

if __name__ == "__main__":
    generate_report()
