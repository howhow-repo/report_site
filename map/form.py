import os, json
from datetime import datetime, timedelta
from django import forms
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


hour_field = [(h, h) for h in range(25)]


class DateInput(forms.DateInput):
    input_type = "date"


def get_rids(sc: StationCenter) -> list:
    rids = []
    rdf = sc.get_routes_ch_name()
    for i in range(len(rdf['rid'])):
        r = (
            rdf['rid'].loc[i],
            rdf['name'].loc[i]
        )
        rids.append(r)
    return rids


def get_rid_select_options():
    sc = StationCenter(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
    sc.connect()
    rids = get_rids(sc)
    sc.disconnect()
    return rids


class ParaInput(forms.Form):
    rid = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=get_rid_select_options())
    )
    rid.label = "路線"

    date_begin = forms.DateField(required=False, widget=DateInput,
                                 initial=lambda: (datetime.now() - timedelta(days=31)))
    date_begin.label = "統計起始日"

    date_end = forms.DateField(required=False, widget=DateInput, initial=lambda: (datetime.today() - timedelta(days=1)))
    date_end.label = "統計截止日"

    hour_begin = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=hour_field)
    )
    hour_begin.label = "統計起始時段(小時)"

    hour_end = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=hour_field),
        initial=24
    )
    hour_end.label = "統計結束時段(小時)"

    weekdayType = forms.TypedMultipleChoiceField(
        required=False,
        coerce=int,
        widget=forms.CheckboxSelectMultiple,
        choices=weekdayType_cn,
        initial=[0, 1, 2, 3, 4, 5, 6]
    )
    weekdayType.label = "計算日種類(複選)"
