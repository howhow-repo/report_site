import json, os
from django import forms
from datetime import datetime, timedelta
from app.reportsLib import StationCenter


def get_rid_select_options(sc: StationCenter) -> list:
    rids = []
    rdf = sc.get_routes_ch_name()
    for i in range(len(rdf['rid'])):
        r = (
            [rdf["rid"].loc[i], rdf["name"].loc[i]],
            rdf["name"].loc[i]
        )
        rids.append(r)
    return rids


sc = StationCenter(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
sc.connect()
rids = get_rid_select_options(sc)
sc.disconnect()

weekdayType_cn = (
    (0, "平日"),
    (1, "週末"),
    (2, "國定假日"),
    (3, "彈性放假"),
    (4, "補假"),
    (5, "補班"),
    (6, "特殊假日"),
)

hour_field = [(h, h) for h in range(25)]


class DateInput(forms.DateInput):
    input_type = "date"


class ParaInput(forms.Form):
    rid_stat = forms.CharField(
        widget=forms.Select(choices=rids)
    )
    rid_stat.label = "路線"

    date_begin = forms.DateField(widget=DateInput, initial=datetime.now() - timedelta(days=31))
    date_begin.label = "統計起始日"

    date_end = forms.DateField(widget=DateInput, initial=datetime.today() - timedelta(days=1))
    date_end.label = "統計截止日"

    hour_begin = forms.IntegerField(
        widget=forms.Select(choices=hour_field)
    )
    hour_begin.label = "統計起始時段(小時)"

    hour_end = forms.IntegerField(
        widget=forms.Select(choices=hour_field),
        initial=24
    )
    hour_end.label = "統計結束時段(小時)"

    weekdayType = forms.IntegerField(
        widget=forms.CheckboxSelectMultiple(choices=weekdayType_cn),
        initial=[0, 1, 2, 3, 4, 5, 6]
    )
    weekdayType.label = "計算日種類(複選)"
