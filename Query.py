# -*- coding: utf-8 -*-

import requests
import numpy as np

class Query(object):

    _sparqlXML = 'application/sparql-results+xml';
    _sparqlJSON = 'application/sparql-results+json';
    _rdfXML = 'application/rdf+xml';
    _rdfJSON = 'application/rdf+json';
    _rdfN3 = 'text/rdf+n3';
    _Html = 'text/html';

    """docstring foResourcme"""

    def __init__(self, _endpoint=''):

        self.endpoint = _endpoint
        self.query = ''

        #static strings 
        # self.API_listOfSpecimens = '''http://api.brain-map.org/api/v2/data/query.json?criteria=model::Specimen,rma::criteria,donor(products[abbreviation$eqHumanASD]),rma::options[num_rows$eq100]'''

        print 'Initialized as %s resource' % (self.endpoint)

        #import SectionImage        
        #self.sectionImage = SectionImage.SectionImage('test')



    def listAllSubjectIDs(self):
        session = requests.Session()
        #session.auth = HTTPDigestAuth(username, password)

        qstring = '''
            PREFIX fs: <http://surfer.nmr.mgh.harvard.edu/fswiki/#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX nidm: <http://nidm.nidash.org/#>
            PREFIX prov: <http://www.w3.org/ns/prov#>

            SELECT DISTINCT ?id where {
                ?c1 fs:subject_id ?id .
            }
            '''


        session.headers = {'Accept':self._sparqlJSON} # HTML from SELECT queries
        data = {'query': qstring}
        result = session.post(self.endpoint, data=data)
        return result.json()['results']['bindings']
    

    def getSubjectDetails(self, subject_id):
        session = requests.Session()

        qstring = '''
        PREFIX fs: <http://surfer.nmr.mgh.harvard.edu/fswiki/#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX nidm: <http://nidm.nidash.org/#>
        PREFIX prov: <http://www.w3.org/ns/prov#>

        select distinct ?structureName ?structureGV where {
             ?subjectCollection fs:subject_id "%s"^^<http://www.w3.org/2001/XMLSchema#string> .
             ?subjectCollection prov:hadMember ?otherMembers .
             ?collectionFromProv prov:wasDerivedFrom ?otherMembers .
             ?collectionFromProv prov:hadMember ?membersOfProvCollection .
             ?membersOfProvCollection a fs:GrayVol . # filter by those that have a type of fs:GrayVol(ume)
             ?membersOfProvCollection fs:structure ?structureName . 
             ?membersOfProvCollection fs:value ?structureGV .
        } ''' % (subject_id)

        session.headers = {'Accept':self._sparqlJSON} # HTML from SELECT queries
        data = {'query': qstring}
        result = session.post(self.endpoint, data=data)
        return result.json()['results']['bindings']


    def getData(self, structure='BA'):
        session = requests.Session()

        qstring = '''
            PREFIX fs: <http://surfer.nmr.mgh.harvard.edu/fswiki/#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX nidm: <http://nidm.nidash.org/#>
            PREFIX prov: <http://www.w3.org/ns/prov#>

            select distinct $id $structure $volume $hemi where {
                ?c1 nidm:annotation "adhd200"^^xsd:string .
                ?c1 fs:subject_id ?id .
                ?c1 prov:hadMember ?f .
                ?f fs:hemisphere ?hemi .
                ?c prov:wasDerivedFrom ?f .
                ?c prov:hadMember ?s .
                ?s a fs:GrayVol .
                ?s fs:structure ?structure .
                ?s fs:value ?volume .
                FILTER regex(str(?structure), "%s")
            }
        ''' % structure

        session.headers = {'Accept':self._sparqlJSON} # HTML from SELECT queries
        data = {'query': qstring}
        result = session.post(self.endpoint, data=data)
        return result.json()['results']['bindings']

        
    def getBoundsFromData(self, data):
        import numpy as np

        # each region will become a coordinate
        # each id will become a coordinate
        # left hemisphere first

        listOfRegions = []
        listOfsubjects = []

        for d in data:
            if d['structure']['value'] not in listOfRegions:
                listOfRegions.append(d['structure']['value'])
            if d['id']['value'] not in listOfsubjects:
                listOfsubjects.append(d['id']['value'])

        return [listOfRegions, listOfsubjects]


    def buildJSONArray(self, data, listOfRegions, listOfsubjects):
        print(len(listOfRegions))
        # 9 regional volumes, 2 per subject id (left/right)
        ad = np.empty((11, len(listOfsubjects)))
        print(ad.shape)

        # 11 total fields: subid, left/right, regional volumes
        lastSub = ''
        subIndex = 0

        for d in data:
            if lastSub != d['id']['value']:
                lastSub = d['id']['value']
                subIndex += 1
            
            ad[0][subIndex - 1] = int(d['id']['value'])
            
            if d['hemi']['value'] == 'left':
                ad[1][subIndex -1] = 0
            else:
                ad[1][subIndex -1] = 1
                
            region_index = listOfRegions.index(d['structure']['value']) + 2
            
            ad[region_index][subIndex - 1] = float(d['volume']['value'])

        return ad


    def getD3pc(self, graphid, datastr):

        js = """
        container.show();
        var kernel = IPython.notebook.kernel;

        var xtkdiv = $('<div id="%s" class="parcoords" style="width:1500px;height:500px"></div>');
        xtkdiv.css('background-color','#fff');
        element.append(xtkdiv);

        var blue_to_brown = d3.scale.linear()
          .domain([0, 1])
          .range(["steelblue", "brown"])
          .interpolate(d3.interpolateLab);

        var color = function(d) { return blue_to_brown(d[1]); };

        var brushListener = function(event) { 
            kernel.execute("brushed_selection=" + JSON.stringify(event))
            };

        d3.parcoords()("#%s")
            .data(%s)
            .color(color)
            .alpha(0.4)
            .render()
            .shadows()
            .brushable()  // enable brushing
            .on('brush', brushListener);

        // load csv file and create the chart
        //d3.csv('files/cars.csv', function(data) {
        //}); 

        """ % (graphid, graphid, datastr)

        return js

            


    # def convertToArray(self, arrayToConvert):
    #     labelarray = []
    #     valuearray = np.zeros(len(jsongraph['bindings']), dtype='f')
    #     indarray = np.arange(len(jsongraph['bindings']))
                                           

    #     for n,val in enumerate(jsongraph['bindings']):
    #     #    data_to_plot.append([val['structureName']['value'], float(val['structureGV']['value'])])
    #         labelarray.append(val['structureName']['value'])
    #         valuearray[n] = float(val['structureGV']['value'])



# select distinct $id $w $x where {
#                 ?c1 nidm:annotation "sad"^^xsd:string .
#                 ?c1 fs:subject_id ?id .
#                 ?c1 prov:hadMember ?f .
#                 ?c prov:wasDerivedFrom ?f .
#                 ?c prov:hadMember ?s .
#                 ?s a ?m .
#                 ?s fs:structure ?w .
#                 ?s fs:value ?x 
#                 FILTER regex(str(?m), fs:ICV)
# }

# get all subject ids
