import json
import os
from datetime import datetime, timedelta
from django import forms
from .reportsLib import StationCenter


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


def get_vids(sc: StationCenter) -> list:
    vids = []
    vdf = sc.get_vids_ch_name()
    for i in range(len(vdf['vid'])):
        v = (
            vdf['vid'].loc[i],
            vdf['name'].loc[i]
        )
        vids.append(v)
    return vids


def get_vid_select_options():
    sc = StationCenter(sqlOption=json.loads(os.getenv("EBUS_SQLDB")))
    sc.connect()
    vids = get_vids(sc)
    sc.disconnect()
    return vids


class DateInput(forms.DateInput):
    input_type = "date"


class ParaInput(forms.Form):
    start_time = forms.DateField(
        required=False,
        widget=DateInput,
        initial=lambda: (datetime.today() - timedelta(days=1)),
        label="統計起始日"
    )

    end_time = forms.DateField(
        required=False,
        widget=DateInput,
        initial=lambda: (datetime.today() - timedelta(days=1)),
        label="統計截止日"
    )

    carno = forms.CharField(
        required=False,
        initial="117-FX",
        label="車號"
    )

    vid = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=get_vid_select_options()),
        label="營運商"
    )

    rid = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=get_rid_select_options()),
        label="路線"
    )

    off_duty_tol = forms.IntegerField(
        required=False,
        initial=1200,
        label="脫班"
    )

    early_tol = forms.IntegerField(
        required=False,
        initial=60,
        label="早發"
    )

    delay_tol = forms.IntegerField(
        required=False,
        initial=300,
        label="遲發"
    )
