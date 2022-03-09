from celery import shared_task, current_task, group, chord, chain
from SPARQLWrapper import SPARQLWrapper, JSON
import datetime
from lxml import html
import requests
import time
import random
import os
import math
from dateutil.parser import parse as parse_date
from typing import Union
import re

from django.conf import settings
from .models import IRSPerson, List, ListEntry
from apis_core.helper_functions.RDFParser import RDFParser
from oebl_irs_workflow.models import Lemma, LemmaStatus, IssueLemma, Issue
from .serializers import ListEntrySerializer
from oebl_irs_workflow.serializers import IssueLemmaSerializer


def create_child_from_parent_model(child_cls, parent_obj, init_values: dict):
    attrs = {}
    for field in parent_obj._meta._get_fields(reverse=False, include_parents=True):
        if (
            field.attname not in attrs
            and not field.attname.endswith("_set")
            and field.attname not in ["text", "title", "profession", "collection"]
        ):
            attrs[field.attname] = getattr(parent_obj, field.attname)
    attrs[child_cls._meta.parents[parent_obj.__class__].name] = parent_obj
    attrs.update(init_values)
    print(attrs)
    return child_cls(**attrs)


# create_child_from_parent_model(ExtendedUser, auth_user, {})


@shared_task(time_limit=500)
def post_results(ccc, listentry_id=[]):
    if isinstance(listentry_id, int):
        listentry_id = [listentry_id]
    list_entry = ListEntry.objects.filter(pk__in=listentry_id)
    header = {"X-Secret": os.environ.get("FRONTEND_CORS_TOKEN", "")}
    obj_data = ListEntrySerializer(list_entry, many=True).data
    res = requests.post(
        os.environ.get(
            "FRONTEND_POST_FINISHED",
            "https://oebl-research.acdh-dev.oeaw.ac.at/message/import-lemmas",
        ),
        headers=header,
        json=obj_data,
    )

    return f"Posted result for {listentry_id} to frontend resulted in {res.status_code}"


@shared_task(time_limit=500)
def post_results_issuelemma(issuelemma_id):
    if isinstance(issuelemma_id, int):
        issuelemma_id = [issuelemma_id]
    issuelemma_entry = IssueLemma.objects.filter(pk__in=issuelemma_id)
    header = {"X-Secret": os.environ.get("FRONTEND_CORS_TOKEN", "")}
    obj_data = IssueLemmaSerializer(issuelemma_entry, many=True).data
    res = requests.post(
        os.environ.get(
            "FRONTEND_POST_FINISHED_ISSUELEMMA",
            "https://oebl-research.acdh-dev.oeaw.ac.at/message/import-issue-lemmas",
        ),
        headers=header,
        json=obj_data,
    )

    return f"Posted result for IssueLemmas {issuelemma_id} to frontend resulted in {res.status_code}"


@shared_task(time_limit=500)
def create_columns(listentry_id, kind="obv"):
    list_entry = ListEntry.objects.get(pk=listentry_id)
    cols = dict()
    if kind == "obv":
        pers_name = list_entry.person.name
        cols["count_obv"] = len(list_entry.scrape["obv"])
        counts_author = 0
        counts_coauthor = 0
        list_co_authors = []
        counts_topic = 0
        counts_topic_authors = 0
        lst_topic_authors = []
        for ent in list_entry.scrape["obv"]:
            test_author = False
            test_coauthor = []
            if "creator" in ent.keys():
                for c1 in ent["creator"]:
                    if pers_name in c1:
                        counts_author += 1
                        test_author = True
                    else:
                        test_coauthor.append(c1)
                if test_author:
                    if len(test_coauthor) > 0:
                        for c3 in test_coauthor:
                            if c3 not in list_co_authors:
                                list_co_authors.append(c3)
                                counts_coauthor += 1
                else:
                    if len(test_coauthor) > 0:
                        for c3 in test_coauthor:
                            if c3 not in lst_topic_authors:
                                lst_topic_authors.append(c3)
                                counts_topic_authors += 1
                    counts_topic += 1
            elif "contributor" in ent.keys():
                counts_topic += 1
                for c2 in ent["contributor"]:
                    if pers_name not in c2 and c2 not in lst_topic_authors:
                        counts_topic_authors += 1
                        lst_topic_authors.append(c2)
        cols["count_author"] = counts_author
        cols["count_coauthor"] = counts_coauthor
        cols["list_coauthors"] = list_co_authors
        cols["count_topic"] = counts_topic
        cols["count_topic_authors"] = counts_topic_authors
        cols["list_topic_authors"] = lst_topic_authors
        list_entry.columns_scrape["obv"] = cols
    else:
        list_entry.columns_scrape[kind] = list_entry.scrape[kind]
    list_entry.save()

    return f"created scrape columns for {listentry_id}"


@shared_task(time_limit=500)
def create_entries(
    entries, listentry_id, scrape_id, *args, kind="obv", multi=True, **kwargs
):
    list_entry = ListEntry.objects.get(pk=listentry_id)
    if multi:
        list_entry.scrape[kind].append(entries)
    else:
        list_entry.scrape[kind] = entries
    list_entry.save()
    create_columns.delay(listentry_id, kind)
    return f"created scrape entries for {scrape_id} / {kind}"


@shared_task(
    time_limit=1000, queue="limited_queue", routing_key="limited_queue.get_obv"
)
def get_obv_records(
    gnd, name, pers_id, listentry_id, scrape_id, *args, limit=50, **kwargs
):
    print(f"searching obv: {gnd}")
    token = requests.get(
        "https://search.obvsg.at/primo_library/libweb/webservices/rest/v1/guestJwt/OBV?isGuest=true&lang=de_DE&targetUrl=https%3A%2F%2Fsearch.obvsg.at%2Fprimo-explore%2Fsearch%3Fvid%3DOBV&viewId=OBV"
    ).json()

    url = "https://search.obvsg.at/primo_library/libweb/webservices/rest/primo-explore/v1/pnxs"

    querystring = {
        "blendFacetsSeparately": "false",
        "getMore": "0",
        "inst": "OBV",
        "lang": "de_DE",
        "limit": limit,
        "mode": "advanced",
        "newspapersActive": "false",
        "newspapersSearch": "false",
        "offset": "0",
        "pcAvailability": "false",
        "q": f"any,contains,{gnd},AND",
        "qExclude": "",
        "qInclude": "",
        "refEntryActive": "false",
        "rtaLinks": "false",
        "scope": "OBV_Gesamt",
        "skipDelivery": "Y",
        "sort": "rank",
        "tab": "default_tab",
        "vid": "OBV",
    }
    headers = {"authorization": f"Bearer {token}"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    if response.status_code == 200:
        res = response.json()
        fin = []
        for r in res["docs"]:
            fin.append(r["pnx"]["display"])
        res_nb = int(res["info"]["total"])
        pages = math.ceil(res_nb / limit)
        if pages < 1:
            pages = 1
        pg = 1
        while pg <= pages:
            querystring["offset"] = limit * (pg - 1)
            response = requests.request("GET", url, headers=headers, params=querystring)
            if response.status_code == 200:
                res = response.json()
                for r in res["docs"]:
                    fin.append(r["pnx"]["display"])
            pg += 1
            time.sleep(random.randrange(2, 5))
        create_entries.delay(fin, listentry_id, scrape_id, multi=False)
    time.sleep(random.randrange(2, 8))

    return f"obv resolved for {gnd}"


@shared_task(time_limit=1000)
def get_wikipedia_entry(
    url, gnd, name, pers_id, listentry_id, scrape_id, *args, **kwargs
):
    try:
        url_version_hist = f"https://de.wikipedia.org/w/index.php?title={url.split('/')[-1]}&offset=&limit=500&action=history"
        vers_hist_page = requests.get(url_version_hist)
        tree_vers_hist = html.fromstring(vers_hist_page.content)
        vers_hist_entries = tree_vers_hist.xpath('//*[@id="pagehistory"]/ul/li')
        count_vers = len(vers_hist_entries)
        count_editors = [
            x.xpath('.//span[@class="history-user"]/a/@href')[0]
            for x in vers_hist_entries
        ]
        count_editors = len(list(dict.fromkeys(count_editors)))
        next_link = tree_vers_hist.xpath('//*[@id="mw-content-text"]/a[@rel="next"]')
        print(next_link)
        while len(next_link) > 0:
            vers_hist_page = requests.get(
                "https://de.wikipedia.org" + next_link[0].get("href")
            )
            print(vers_hist_page)
            tree_vers_hist = html.fromstring(vers_hist_page.content)
            vers_hist_entries = tree_vers_hist.xpath('//*[@id="pagehistory"]/ul/li')
            count_vers += len(vers_hist_entries)
            count_editors_1 = [
                x.xpath('.//span[@class="history-user"]/a/@href')[0]
                for x in vers_hist_entries
            ]
            count_editors += len(list(dict.fromkeys(count_editors_1)))
            next_link = tree_vers_hist.xpath(
                '//*[@id="mw-content-text"]/a[@rel="next"]'
            )
            print(next_link)
        print(count_vers)
    except Exception as e:
        print(e)
        count_editors = "Not available"
        count_vers = "Not available"
    page = requests.get(url)
    tree = html.fromstring(page.content)
    txt = tree.xpath('.//div[@class="mw-parser-output"]')[0].text_content()
    fin = {"edits_count": count_vers, "number_of_editors": count_editors, "txt": txt}
    create_entries.delay(fin, listentry_id, scrape_id, kind="wikipedia", multi=False)

    return f"wikipedia resolved for {url}"


@shared_task(time_limit=1000)
def get_wikidata_records(gnd, name, pers_id, listentry_id, scrape_id, *args, **kwargs):
    query = f"""
    SELECT ?p ?pLabel ?date_of_birth ?date_of_death ?ndb ?loc ?viaf ?wiki_de ?parlAT ?wienWiki (GROUP_CONCAT(?ausz2;SEPARATOR=", ") AS ?auszeichnungen)
        WHERE {{
          ?p wdt:P227 "{gnd}".
          OPTIONAL {{ ?p wdt:P7902 ?ndb }}
          OPTIONAL {{ ?p wdt:P244 ?loc }}
          OPTIONAL {{ ?p wdt:P2280 ?parlAT }}
          OPTIONAL {{ ?p wdt:P7842 ?wienWiki }}
          OPTIONAL {{ ?p wdt:P569 ?date_of_birth }}
          OPTIONAL {{ ?p wdt:P570 ?date_of_death }}
          OPTIONAL {{ ?p wdt:P214 ?viaf }}
          OPTIONAL {{ ?wiki_de schema:about ?p .
            ?wiki_de schema:inLanguage "de" .
            ?wiki_de schema:isPartOf <https://de.wikipedia.org/> }}
          OPTIONAL {{ ?p wdt:P166 ?ausz2 }}
             SERVICE wikibase:label {{
             bd:serviceParam wikibase:language "[AUTO_LANGUAGE], de" .
           }}
          }}
        GROUP BY ?p ?pLabel ?date_of_birth ?date_of_death ?ndb ?loc ?viaf ?wiki_de ?parlAT ?wienWiki
    """
    sparqlwd = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparqlwd.setQuery(query)
    sparqlwd.setReturnFormat(JSON)
    results = sparqlwd.query().convert()
    fin = dict()
    if len(results["results"]["bindings"]) > 0:
        for k, v in results["results"]["bindings"][0].items():
            fin[k] = v["value"]
        create_entries.delay(fin, listentry_id, scrape_id, kind="wikidata", multi=False)
        if "wiki_de" in fin.keys() and kwargs["include_wikipedia"]:
            get_wikipedia_entry.delay(
                fin["wiki_de"], gnd, name, pers_id, listentry_id, scrape_id
            )
    return f"wikidata resolved for {gnd}"


default_scrapes = [get_wikidata_records, get_obv_records]
scrapes_names = ["obv", "wikipedia", "wikidata"]
system_cols = ["id", "gnd", "firstName", "lastName", "dateOfBirth", "dateOfDeath"]


def normalize_date(date: Union[str, None]) -> Union[datetime.date, None]:
    if date is None:
        return None
    else:
        res = parse_date(date)
        if isinstance(res, datetime.date):
            return res
        else:
            return None


@shared_task(time_limit=2000, bind=True)
def scrape(
    self,
    obj,
    user_id,
    list_id,
    scrapes=default_scrapes,
    wiki=True,
    update=False,
    gnd_job=False,
):
    scrape_id = self.request.id
    obj_scrape = []
    obj_save = []
    lst = List.objects.get(pk=list_id)
    for idx, ent in enumerate(obj["lemmas"]):
        if not update:
            test_gnd = False #TODO: move to dedicated serializer function
            ent_dict = {
                "first_name": ent.get("firstName", "-"),
                "name": ent.get("lastName", "-"),
                "date_of_birth": normalize_date(ent.get("dateOfBirth", None)),
                "date_of_death": normalize_date(ent.get("dateOfDeath", None)),
                "gender": ent.get("gender", None),
                "alternative_names": ent.get("alternativeNames", []),
                "uris": [],
            }
            if "gnd" in ent.keys():
                gnds = []
                if isinstance(ent["gnd"], str):
                    ent["gnd"] = [ent["gnd"]]
                for g in ent["gnd"]:
                    ent_dict["uris"].append(f"https://d-nb.info/gnd/{g}/")
                    gnds.append(g)
                if len(gnds) == 1:
                    test_gnd = True
            list_entry_dict = dict()
            dict_user_cols = {}
            for k, v in ent.items():
                if k not in system_cols:
                    dict_user_cols[k] = v
            list_entry_dict["columns_user"] = dict_user_cols
            if "id" in ent.keys():
                list_entry_dict["source_id"] = ent["id"] if ent["id"] > 0 else idx
            else:
                list_entry_dict["source_id"] = idx
            pers, created = IRSPerson.objects.get_or_create(**ent_dict)
            list_entry_dict["person_id"] = pers.pk
            list_entry_dict["list_id"] = lst.pk
            list_entry_dict["selected"] = ent.get("selected", False)
            list_entry_dict["columns_scrape"] = {
                "obv": [],
                "wikipedia": [],
                "wikidata": [],
            }
            list_entry_dict["scrape"] = {"obv": [], "wikipedia": [], "wikidata": []}
            list_entry = ListEntry.objects.create(**list_entry_dict)
        if update:
            list_entry = ListEntry.objects.get(pk=update)
            pers = list_entry.person
            gnds = gnd_job
            test_gnd = len(gnds) == 1
        if test_gnd:
            obj_scrape.append((gnds[0], ent, pers, list_entry))
        else:
            obj_save.append(list_entry)
    if len(obj_save) > 0:
        res_obj_save = post_results.delay("test", listentry_id=[x.pk for x in obj_save])
    res = group(
        chord(
            (
                scr.s(
                    entry[0],
                    f"{entry[1].get('lastName', '-')}, {entry[1].get('firstName', '-')}",
                    entry[2].pk,
                    entry[3].pk,
                    scrape_id,
                    include_wikipedia=wiki,
                )
                for scr in scrapes
            ),
            post_results.s(entry[3].pk),
        )
        for entry in obj_scrape
    )()
    return f"started job for {user_id}"


class EntityAlreadyExists(Exception):
    pass


@shared_task(time_limit=500)
def create_new_workflow_lemma(
    editor_id, research_lemma_id, gnd=None, person_attrb={}, issue_id=None
):
    if gnd:
        try:
            pers = RDFParser(gnd, "Person").get_or_create()
            if not pers:
                raise EntityAlreadyExists(f"{gnd} already in db")
            workflow_lemma = create_child_from_parent_model(
                Lemma, pers, person_attrb
            ).save()
        except:
            workflow_lemma = Lemma.objects.create(**person_attrb)
    else:
        workflow_lemma = Lemma.objects.create(**person_attrb)
    lemma_status, created = LemmaStatus.objects.get_or_create(name="angelegt")
    lemma_issue = {
        "status_id": lemma_status.pk,
        "editor_id": editor_id,
        "issue_id": issue_id,
        "lemma_id": workflow_lemma.pk,
    }
    il = IssueLemma.objects.create(**lemma_issue)
    research_lemma = IRSPerson.objects.get(pk=research_lemma_id)
    research_lemma.irs_person = workflow_lemma
    research_lemma.save()
    return il.pk


@shared_task(time_limit=500)
def move_research_lemmas_to_workflow(editor_id, lst_research_lemmas, issue=None):
    # if issue:
    #    issue1, created = Issue.objects.get_or_create(**issue)
    #    issue = issue1.pk
    p_list = []
    le_list = []
    for lm in lst_research_lemmas:
        le = ListEntry.objects.get(pk=lm)
        le_list.append(le.pk)
        gnd = False
        for uri in le.person.uris:
            if "d-nb.info" in uri:
                gnd = uri
        person_attrb = le.get_dict()
        p_list.append((editor_id, le.person_id, gnd, person_attrb, issue))
    res = chord(
        (create_new_workflow_lemma.s(*p1) for p1 in p_list),
        post_results_issuelemma.s(),
    )()
    return f"moved lemmas to Workflow tool"
