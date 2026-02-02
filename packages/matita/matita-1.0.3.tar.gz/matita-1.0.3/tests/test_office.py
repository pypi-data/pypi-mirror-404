import inspect
import unittest

from matita.office import access as ac, excel as xl, outlook as ol, powerpoint as pp, word as wd


class TestAccess(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.ac_app = ac.Application()
        cls.ac_app.Visible = True

    @classmethod
    def tearDownClass(cls):
        cls.ac_app.Quit()
    
    def test_aliases(self):
        membs = inspect.getmembers(ac.Application)
        membs = [m[0] for m in membs.copy()]
        # Parameter
        self.assertIn("AppIcon", membs)
        self.assertIn("appicon", membs)
        self.assertIn("app_icon", membs)
        #Method
        self.assertIn("FileDialog", membs)
        self.assertIn("filedialog", membs)
        self.assertIn("file_dialog", membs)

    def test_access_visibility(self):
        self.assertTrue(self.ac_app.Visible)

class TestExcel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.xl_app = xl.Application()
        cls.xl_app.visible = True

    @classmethod
    def tearDownClass(cls):
        cls.xl_app.Quit()

    def test_hello_world(self):
        wkb = self.xl_app.workbooks.Add()
        wks = wkb.worksheets(1)
        c = wks.cells(1,1)
        c.value = "Hello world!"
        self.assertEqual(c.com_object.Value, "Hello world!")
        wkb.Close(SaveChanges=False)

    def test_item_return_type(self):
        wkb = self.xl_app.workbooks.add()
        self.assertIsInstance(self.xl_app.workbooks(1), xl.Workbook)
        self.assertIsInstance(self.xl_app.workbooks.item(1), xl.Workbook)
        self.assertIsInstance(wkb.worksheets(1), xl.Worksheet)
        self.assertIsInstance(wkb.worksheets.item(1), xl.Worksheet)

        rng = wkb.worksheets(1).cells(1,1)
        
        self.assertIsInstance(rng.Areas(1), xl.Range)
        self.assertIsInstance(rng.Areas.item(1), xl.Range)
        self.assertIsInstance(rng.Columns(1), xl.Range)
        self.assertIsInstance(rng.Columns.item(1), xl.Range)
        self.assertIsInstance(rng.Rows(1), xl.Range)
        self.assertIsInstance(rng.Rows.item(1), xl.Range)

        wkb.Close(SaveChanges=False)

    def test_excel_types(self):
        wkb = self.xl_app.workbooks.add()
        wks = wkb.worksheets(1)

        cell_str = wks.range("A1")
        cell_int = wks.range("A2")
        cell_float = wks.range("A3")
        cell_bool = wks.range("A4")

        cell_str.value = "ciao"
        cell_int.value = 123
        cell_float.value = 3.14159
        cell_bool.value = True

        self.assertEqual(cell_str.value, "ciao")
        self.assertEqual(cell_int.value, 123)
        self.assertAlmostEqual(cell_float.value, 3.14159)
        self.assertEqual(cell_bool.value, True)
        self.assertIs(type(wks.list_objects), xl.ListObjects)

        wkb.Close(SaveChanges=False)

    def test_range_address(self):
        wkb = self.xl_app.Workbooks.Add()
        wks = wkb.Worksheets(1)

        r = wks.range("B2:D4")
        self.assertEqual(r.Address(), "$B$2:$D$4")
        self.assertEqual(r.address(), "$B$2:$D$4")
        self.assertEqual(r.Address(ReferenceStyle=xl.xlR1C1), "R2C2:R4C4")
        self.assertEqual(r.address(ReferenceStyle=xl.xlR1C1), "R2C2:R4C4")

        wkb.Close(SaveChanges=False)

    def test_excel_aliases(self):
        wkb = self.xl_app.Workbooks.Add()

        self.assertIs(type(wkb.Worksheets.Add()), xl.Worksheet)
        self.assertIs(type(wkb.Worksheets.add()), xl.Worksheet)

        wkb.Close(SaveChanges=False)

    def test_excel_constants(self):
        self.assertEqual(xl.xlAscending, 1)
        self.assertEqual(xl.xlDescending, 2)

    def test_excel_com_object(self):
        wkb = self.xl_app.Workbooks.Add()
        self.assertIs(type(wkb), xl.Workbook)
        self.assertIn("win32", str(type(wkb.com_object)))
        wkb.Close(SaveChanges=False)

    def test_range_operations(self):
        wkb = self.xl_app.Workbooks.Add()
        wks = wkb.worksheets(1)
        rng = wks.cells(2,3)
        self.assertEqual(rng.resize(4,5).address(), "$C$2:$G$5")

        rng = wks.range("$A$1:$C$2")
        self.assertEqual(rng.offset(2,3).address(), "$D$3:$F$4")

        cell1 = wks.cells(2,2)
        cell2 = wks.cells(5,5)
        rng = wks.range(cell1, cell2)
        self.assertEqual(rng.address(), "$B$2:$E$5")

        rng1 = wks.range("B2:D5")
        rng2 = wks.range("C4:E7")
        rng = self.xl_app.intersect(rng1, rng2)
        self.assertEqual(rng.address(), "$C$4:$D$5")

        cell1 = wks.cells(1,1)
        cell2 = wks.cells(2,2)
        rng = self.xl_app.intersect(cell1, cell2)
        self.assertIsNone(rng.com_object)
        wkb.Close(SaveChanges=False)
    
    def test_charts(self):
        wkb = self.xl_app.Workbooks.Add()
        wks = wkb.worksheets(1)
        # Add at least one value to the worksheet, otherwise the SeriesCollection will be empty
        wks.cells(1,1).value = 12345 
        chart = wks.shapes.add_chart2(XlChartType=xl.xlLineMarkers).chart
        # set
        self.assertIs(type(chart.full_series_collection()), xl.FullSeriesCollection)
        self.assertIs(type(chart.full_series_collection().item(1)), xl.Series)
        self.assertIs(type(chart.full_series_collection()(1)), xl.Series)
        self.assertIs(type(chart.full_series_collection(1)), xl.Series)
        # collection - fails, depends on backlog item 9 to work
        # self.assertIs(type(chart.series_collection()), xl.SeriesCollection)
        # self.assertIs(type(chart.series_collection().item(1)), xl.Series)
        # self.assertIs(type(chart.series_collection(1)), xl.Series)
        
        wkb.Close(SaveChanges=False)


class TestOutlook(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ol_app = ol.Application()

    @classmethod
    def tearDownClass(cls):
        cls.ol_app.Quit()
        
    def test_hello_world(self):
        mail = ol.MailItem(self.ol_app.create_item(ol.olMailItem))
        mail.body = "Hello world!"
        self.assertTrue(mail.com_object.Body.startswith("Hello world!"))

class TestPowerPoint(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.pp_app = pp.Application()
        cls.pp_app.visible = True

    @classmethod
    def tearDownClass(cls):
        cls.pp_app.Quit()

    def test_hello_world(self):
        prs = self.pp_app.presentations.add()
        sld = prs.slides.add(1, pp.ppLayoutBlank)
        shp = sld.shapes.add_shape(pp.msoShapeRectangle, 30, 30 , 30, 30)
        shp.text_frame.text_range.text = "Hello world!"
        self.assertEqual(shp.text_frame.text_range.com_object.Text, "Hello world!")
        prs.close()

    def test_powerpoint(self):
        self.assertTrue(self.pp_app.visible)
        prs = self.pp_app.presentations.add()
        sld = prs.slides.add(1, pp.ppLayoutBlank)
        shp = sld.shapes.add_shape(pp.msoShapeRectangle, 30, 30 , 30, 30)
        eff = sld.timeline.main_sequence.add_effect(
            Shape=shp,
            effectId=pp.msoAnimEffectFly,
            Level=pp.msoAnimateLevelNone,
            trigger=pp.msoAnimTriggerAfterPrevious,
        )
        prs.close()
        
    def test_powerpoint_com_object(self):
        prs = self.pp_app.presentations.add()
        self.assertIs(type(prs), pp.Presentation)
        self.assertIn("win32", str(type(prs.com_object)))
        prs.close()

class TestWord(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.wd_app = wd.Application()
        cls.wd_app.visible = True

    @classmethod
    def tearDownClass(cls):
        cls.wd_app.Quit(SaveChanges=wd.wdDoNotSaveChanges)

    def test_hello_world(self):
        doc = self.wd_app.documents.add()
        par = doc.content.paragraphs.add()
        par.range.text = "Hello world!"
        self.assertTrue(par.range.com_object.Text.startswith("Hello world!"))
