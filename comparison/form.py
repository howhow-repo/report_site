import json, os
from django import forms
from datetime import datetime, timedelta
from app.reportsLib import StationCenter

weekdayType_cn = [
    (0, "平日"),
    (1, "週末"),
    (2, "國定假日"),
    (3, "彈性放假"),
    (4, "補假"),
    (5, "補班"),
    (6, "特殊假日"),
]

weekday_cn = [
    (0, "星期一"),
    (1, "星期二"),
    (2, "星期三"),
    (3, "星期四"),
    (4, "星期五"),
    (5, "星期六"),
    (6, "星期日"),
]

hour_field = [(h, h) for h in range(25)]


def get_rids(sc: StationCenter) -> list:
    rids = []
    rdf = sc.get_routes_ch_name()
    for i in range(len(rdf['rid'])):
        r = (
            [rdf["rid"].loc[i], rdf["name"].loc[i]],
            rdf["name"].loc[i]
        )
        rids.append(r)
    return rids


def get_rid_select_options():
    sc = StationCenter(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
    sc.connect()
    rids = get_rids(sc)
    sc.disconnect()
    return sorted(rids)


class DateInput(forms.DateInput):
    input_type = "date"


class ParaInput(forms.Form):
    rid_stat = forms.CharField(
        required=False,
        widget=forms.Select(choices=get_rid_select_options())
    )
    rid_stat.label = "路線"

    rsid = forms.IntegerField(required=False)
    rsid.label = "路線站ID(rsid)"

    date_begin = forms.DateField(required=False,widget=DateInput, initial=lambda: (datetime.now() - timedelta(days=61)))
    date_begin.label = "統計起始日"

    date_end = forms.DateField(required=False,widget=DateInput, initial=lambda: (datetime.today() - timedelta(days=1)))
    date_end.label = "統計截止日"

    hour_begin = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=hour_field),
        initial=0
    )
    hour_begin.label = "統計起始時段(小時)"

    hour_end = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=hour_field),
        initial=24
    )
    hour_end.label = "統計結束時段(小時)"

    weekday_A = forms.TypedMultipleChoiceField(
        required=False,
        coerce=int,
        widget=forms.CheckboxSelectMultiple,
        choices=weekday_cn,
        initial=[0],
    )
    weekday_A.label = "星期(複選)"

    weekdayType_A = forms.TypedMultipleChoiceField(
        required=False,
        coerce=int,
        widget=forms.CheckboxSelectMultiple,
        choices=weekdayType_cn,
        initial=[0, 1, 2, 3, 4, 5, 6]
    )
    weekdayType_A.label = "計算日種類(複選)"

    weekday_B = forms.TypedMultipleChoiceField(
        required=False,
        coerce=int,
        widget=forms.CheckboxSelectMultiple,
        choices=weekday_cn,
        initial=[0]
    )
    weekday_B.label = "星期(複選)"

    weekdayType_B = forms.TypedMultipleChoiceField(
        required=False,
        coerce=int,
        widget=forms.CheckboxSelectMultiple,
        choices=weekdayType_cn,
        initial=[0, 1, 2, 3, 4, 5, 6]
    )
    weekdayType_B.label = "計算日種類(複選)"

