class ComparisonReportBase:
    rtype = None
    title = None
    description = ''
    paras_comm = []
    paras_A = []
    paras_B = []
    compare_value = ''


class TraveltimeWeekday(ComparisonReportBase):
    rtype = 'traveltime_weekday'
    title = '行駛時間與星期比較表'
    description = '比較不同星期時，站與站之間的行駛時間。'
    paras_comm = ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end']
    paras_A = ['weekday_A'],
    paras_B = ['weekday_B'],
    compare_value = 'avg_arrival_time_spent'


class TraveltimeWeekdayType(ComparisonReportBase):
    rtype = 'traveltime_weekdayType'
    title = '行駛時間與日種類比較表'
    description = '比較不同種日時，站與站之間的行駛時間。'
    paras_comm = ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end']
    paras_A = ['weekdayType_A'],
    paras_B = ['weekdayType_B'],
    compare_value = 'avg_arrival_time_spent'


class StaytimeWeekday(ComparisonReportBase):
    rtype = 'traveltime_weekdayType'
    title = '站內停留時間與星期比較表'
    description = '比較不同星期時，站內停留時間。'
    paras_comm = ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end']
    paras_A = ['weekday_A'],
    paras_B = ['weekday_B'],
    compare_value = 'avg_stay_time'


class StaytimeWeekdayType(ComparisonReportBase):
    rtype = 'staytime_weekdayType'
    title = '站內停留時間與日種類比較表'
    description = '比較不同種日時，站內停留時間。'
    paras_comm = ['rid_stat', 'date_begin', 'date_end', 'hour_begin', 'hour_end']
    paras_A = ['weekdayType_A'],
    paras_B = ['weekdayType_B'],
    compare_value = 'avg_stay_time'


class RsidTraveltimeWeekday(ComparisonReportBase):
    rtype = 'rsid_traveltime_weekday'
    title = '單站行駛時間與星期比較表'
    description = '比較兩站之間，在不同星期下的行駛時間。'
    paras_comm = ['rsid', 'date_begin', 'date_end', ],
    paras_A = ['weekday_A'],
    paras_B = ['weekday_B'],
    compare_value = 'avg_arrival_time_spent'


class RsidTraveltimeWeekdayType(ComparisonReportBase):
    rtype = 'rsid_traveltime_weekdayType'
    title = '單站行駛時間與日種類比較表'
    description = '比較兩站之間，在不同日種類下的行駛時間。'
    paras_comm = ['rsid', 'date_begin', 'date_end', ],
    paras_A = ['weekdayType_A'],
    paras_B = ['weekdayType_B'],
    compare_value = 'avg_arrival_time_spent'


class RsidStaytimeWeekday(ComparisonReportBase):
    rtype = 'rsid_staytime_weekday'
    title = '單站停留時間與星期比較表'
    description = '比較同一站，在不同星期下的行駛時間。'
    paras_comm = ['rsid', 'date_begin', 'date_end', ],
    paras_A = ['weekday_A'],
    paras_B = ['weekday_B'],
    compare_value = 'avg_stay_time'


class RsidStaytimeWeekdayType(ComparisonReportBase):
    rtype = 'rsid_staytime_weekdayType'
    title = '單站停留時間與日種類比較表'
    description = '比較同一站，在不同日種類下的行駛時間。'
    paras_comm = ['rsid', 'date_begin', 'date_end', ],
    paras_A = ['weekdayType_A'],
    paras_B = ['weekdayType_B'],
    compare_value = 'avg_stay_time'


class ComparisonReportCenter:
    report_list = [
        TraveltimeWeekday,
        TraveltimeWeekdayType,
        StaytimeWeekday,
        StaytimeWeekdayType,
        RsidStaytimeWeekdayType,
        RsidStaytimeWeekday,
        RsidTraveltimeWeekdayType,
        RsidTraveltimeWeekday,
    ]

    @classmethod
    def list_of_dict(cls) -> list:
        l = []
        for r in cls.report_list:
            t = {}
            r_attr = [a for a in dir(r) if not a.startswith('__')]
            for a in r_attr:
                t.update({a: getattr(r, a)})
            l.append(t)
        return l
