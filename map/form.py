import os, json
from django import forms
from app.reportsLib import StationCenter


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
