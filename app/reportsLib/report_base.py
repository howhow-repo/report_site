import pandas as pd


class ReportBase:
    '''
        Basic functions and args for reports
    '''

    def __init__(self, centerDB_conn_options, drivelogDB_conn_options):
        self._centerDB_conn_options = centerDB_conn_options
        self._drivelogDB_conn_options = drivelogDB_conn_options
        self.title = None
        self.simple_description = ''
        self.sub_title = ''
        self.sub_title2 = ''
        self.report = None
        self.start_time = None
        self.end_time = None

    def generate_report(self, **kwargs):
        raise NotImplementedError

    def parsing_df_for_user(self):
        raise NotImplementedError

    def view_in_html(self):
        raise NotImplementedError

    def generate_daily_report(self, **kwargs):
        raise NotImplementedError

    def save_as_pdf(self, **kwargs):
        raise NotImplementedError

    def show_report(self, _return: bool = False):
        if self.report is None:
            raise TypeError("report haven't been created yet. "
                            "please use method 'create_empty_report(report_name)'")
        print(self.report)
        if _return is True:
            return self.report

    def generate_test_report(self):
        test_report = {'Class name': [self.__class__], 'column 2': ["test report"]}
        self.report = pd.DataFrame(test_report)
        return test_report

    def erase_report(self):
        self.report = None

