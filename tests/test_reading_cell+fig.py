# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import logging
import unittest2
from builtins import bytes

from chemdataextractor import Document

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestAddingCellFigure(unittest2.TestCase):

    """ Test parsing warning for when a figure is nested inside a table and can not be added."""

    def test_reader_adding(self):
        xml_string = """<full-text-retrieval-response xmlns="http://www.elsevier.com/xml/svapi/article/dtd" xmlns:bk="http://www.elsevier.com/xml/bk/dtd" xmlns:cals="http://www.elsevier.com/xml/common/cals/dtd" xmlns:ce="http://www.elsevier.com/xml/common/dtd" xmlns:ja="http://www.elsevier.com/xml/ja/dtd" xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:sa="http://www.elsevier.com/xml/common/struct-aff/dtd" xmlns:sb="http://www.elsevier.com/xml/common/struct-bib/dtd" xmlns:tb="http://www.elsevier.com/xml/common/table/dtd" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xocs="http://www.elsevier.com/xml/xocs/dtd" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:prism="http://prismstandard.org/namespaces/basic/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><coredata><prism:url>https://api.elsevier.com/content/article/pii/S0022072802014705</prism:url><dc:identifier>doi:10.1016/S0022-0728(02)01470-5</dc:identifier><eid>1-s2.0-S0022072802014705</eid><prism:doi>10.1016/S0022-0728(02)01470-5</prism:doi><pii>S0022-0728(02)01470-5</pii><dc:title>Colloidal silver iodide: synthesis by a reverse micelle method and investigation by a small-angle neutron scattering study </dc:title><prism:publicationName>Journal of Electroanalytical Chemistry</prism:publicationName><prism:aggregationType>Journal</prism:aggregationType><pubType>
                       Short Communication
                    </pubType><prism:issn>15726657</prism:issn><prism:volume>559</prism:volume><prism:startingPage>103</prism:startingPage><prism:endingPage>109</prism:endingPage><prism:pageRange>103-109</prism:pageRange><dc:format>text/xml</dc:format><prism:coverDate>2003-11-15</prism:coverDate><prism:coverDisplayDate>15 November 2003</prism:coverDisplayDate><prism:copyright>Copyright © 2003 Elsevier Science B.V. All rights reserved.</prism:copyright><prism:publisher>Elsevier Science B.V.</prism:publisher><prism:issueName>International Symposium on Materials Processing for Nanostructured Devices 2001</prism:issueName><dc:creator>Tamura, Sanae</dc:creator><dc:creator>Takeuchi, Ken</dc:creator><dc:creator>Mao, Guomin</dc:creator><dc:creator>Csencsits, Roseann</dc:creator><dc:creator>Fan, Lixin</dc:creator><dc:creator>Otomo, Toshiya</dc:creator><dc:creator>Saboungi, Marie-Louise</dc:creator><dc:description>
                       Abstract

                          Really Cool Paper

                    </dc:description><openaccess>0</openaccess><openaccessArticle>false</openaccessArticle><openaccessType/><openArchiveArticle>false</openArchiveArticle><openaccessSponsorName/><openaccessSponsorType/><openaccessUserLicense/><dcterms:subject>Nanoparticle</dcterms:subject><dcterms:subject>Reverse micelle method</dcterms:subject><dcterms:subject>Silver iodide</dcterms:subject><dcterms:subject>Small-angle neutron scattering</dcterms:subject><link href="https://api.elsevier.com/content/article/pii/S0022072802014705" rel="self"/><link href="https://www.sciencedirect.com/science/article/pii/S0022072802014705" rel="scidir"/></coredata><objects><object ref="si1" category="thumbnail" type="ALTIMG" multimediatype="GIF image file" mimetype="image/gif" width="121" height="17" size="677">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-si1.gif?httpAccept=%2A%2F%2A</object><object ref="gr1" category="thumbnail" type="IMAGE-THUMBNAIL" multimediatype="GIF image file" mimetype="image/gif" width="125" height="83" size="2435">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr1.sml?httpAccept=%2A%2F%2A</object><object ref="gr1" category="standard" type="IMAGE-DOWNSAMPLED" multimediatype="JPEG image file" mimetype="image/jpeg" width="533" height="352" size="50922">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr1.jpg?httpAccept=%2A%2F%2A</object><object ref="gr2" category="thumbnail" type="IMAGE-THUMBNAIL" multimediatype="GIF image file" mimetype="image/gif" width="119" height="93" size="2537">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr2.sml?httpAccept=%2A%2F%2A</object><object ref="gr2" category="standard" type="IMAGE-DOWNSAMPLED" multimediatype="GIF image file" mimetype="image/gif" width="372" height="292" size="12638">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr2.gif?httpAccept=%2A%2F%2A</object><object ref="fx1" category="thumbnail" type="IMAGE-THUMBNAIL" multimediatype="GIF image file" mimetype="image/gif" width="125" height="41" size="1117">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-fx1.sml?httpAccept=%2A%2F%2A</object><object ref="fx1" category="standard" type="IMAGE-DOWNSAMPLED" multimediatype="JPEG image file" mimetype="image/jpeg" width="696" height="231" size="36815">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-fx1.jpg?httpAccept=%2A%2F%2A</object><object ref="gr3" category="thumbnail" type="IMAGE-THUMBNAIL" multimediatype="GIF image file" mimetype="image/gif" width="125" height="78" size="3128">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr3.sml?httpAccept=%2A%2F%2A</object><object ref="gr3" category="standard" type="IMAGE-DOWNSAMPLED" multimediatype="JPEG image file" mimetype="image/jpeg" width="261" height="163" size="15317">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr3.jpg?httpAccept=%2A%2F%2A</object><object ref="gr4" category="thumbnail" type="IMAGE-THUMBNAIL" multimediatype="GIF image file" mimetype="image/gif" width="125" height="76" size="2491">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr4.sml?httpAccept=%2A%2F%2A</object><object ref="gr4" category="standard" type="IMAGE-DOWNSAMPLED" multimediatype="JPEG image file" mimetype="image/jpeg" width="301" height="182" size="23570">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr4.jpg?httpAccept=%2A%2F%2A</object><object ref="gr5" category="thumbnail" type="IMAGE-THUMBNAIL" multimediatype="GIF image file" mimetype="image/gif" width="125" height="91" size="2140">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr5.sml?httpAccept=%2A%2F%2A</object><object ref="gr5" category="standard" type="IMAGE-DOWNSAMPLED" multimediatype="GIF image file" mimetype="image/gif" width="376" height="273" size="13818">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr5.gif?httpAccept=%2A%2F%2A</object><object ref="gr6" category="thumbnail" type="IMAGE-THUMBNAIL" multimediatype="GIF image file" mimetype="image/gif" width="124" height="93" size="2193">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr6.sml?httpAccept=%2A%2F%2A</object><object ref="gr6" category="standard" type="IMAGE-DOWNSAMPLED" multimediatype="GIF image file" mimetype="image/gif" width="350" height="263" size="9781">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr6.gif?httpAccept=%2A%2F%2A</object><object ref="gr7" category="thumbnail" type="IMAGE-THUMBNAIL" multimediatype="GIF image file" mimetype="image/gif" width="101" height="93" size="1877">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr7.sml?httpAccept=%2A%2F%2A</object><object ref="gr7" category="standard" type="IMAGE-DOWNSAMPLED" multimediatype="GIF image file" mimetype="image/gif" width="363" height="334" size="11999">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr7.gif?httpAccept=%2A%2F%2A</object><object ref="gr8" category="thumbnail" type="IMAGE-THUMBNAIL" multimediatype="GIF image file" mimetype="image/gif" width="124" height="94" size="1998">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr8.sml?httpAccept=%2A%2F%2A</object><object ref="gr8" category="standard" type="IMAGE-DOWNSAMPLED" multimediatype="GIF image file" mimetype="image/gif" width="310" height="234" size="6832">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr8.gif?httpAccept=%2A%2F%2A</object><object ref="gr9" category="thumbnail" type="IMAGE-THUMBNAIL" multimediatype="GIF image file" mimetype="image/gif" width="125" height="90" size="5591">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr9.sml?httpAccept=%2A%2F%2A</object><object ref="gr9" category="standard" type="IMAGE-DOWNSAMPLED" multimediatype="GIF image file" mimetype="image/gif" width="240" height="173" size="16613">https://api.elsevier.com/content/object/eid/1-s2.0-S0022072802014705-gr9.gif?httpAccept=%2A%2F%2A</object></objects><scopus-id>0242405855</scopus-id><scopus-eid>2-s2.0-0242405855</scopus-eid><link href="https://api.elsevier.com/content/abstract/scopus_id/0242405855" rel="abstract"/><originalText><xocs:doc xmlns:xoe="http://www.elsevier.com/xml/xoe/dtd" xsi:schemaLocation="http://www.elsevier.com/xml/xocs/dtd http://null/schema/dtds/document/fulltext/xcr/xocs-article.xsd">

                    <xocs:serial-item>
                    <converted-article xmlns="http://www.elsevier.com/xml/ja/dtd" version="4.5.2" docsubtype="fla" xml:lang="en">

                    <ce:floats>
                    <ce:table xmlns="http://www.elsevier.com/xml/common/cals/dtd" id="TBL1" colsep="0" rowsep="0" frame="none">
                       <ce:label>Table 1</ce:label>
                       <ce:caption>
                          <ce:simple-para view="all">Appearance of microemulsions</ce:simple-para>
                       </ce:caption>
                       <tgroup cols="6">
                          <colspec colname="col1" colsep="0"/>
                          <colspec colname="col2" colsep="0"/>
                          <colspec colname="col3" colsep="0"/>
                          <colspec colname="col4" colsep="0"/>
                          <colspec colname="col5" colsep="0"/>
                          <colspec colname="col6" colsep="0"/>
                          thead>
                             <row>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd"/>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd"/>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd"/>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd"/>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd"/>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd"/>
                             </row>
                          </thead>
                          <tbody>
                             <row>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd">
                                   <display xmlns="http://www.elsevier.com/xml/ja/dtd">
                                      <figure xmlns="http://www.elsevier.com/xml/common/dtd">
                                         <link locator="fx1"/>
                                      </figure>
                                   </display>
                                </entry>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd" align="char" char="."/>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd"/>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd"/>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd"/>
                                <entry xmlns="http://www.elsevier.com/xml/common/dtd"/>
                             </row>
                          </tbody>
                       </tgroup>
                       <ce:legend>
                          <ce:simple-para view="all">
                             <ce:italic>w</ce:italic>, molar ratio of H<ce:inf loc="post">2</ce:inf>O to surfactant=[H<ce:inf loc="post">2</ce:inf>O]/[AOT].</ce:simple-para>
                       </ce:legend>
                    </ce:table>
                    </ce:floats>
                    </converted-article>
                    </xocs:serial-item>
                    </xocs:doc></originalText></full-text-retrieval-response>"""

        with self.assertLogs(level=logging.WARNING) as cm:
            if sys.version_info[0] < 3:
                d = Document().from_string(bytes(xml_string, 'utf-8'))
            else:
                d = Document().from_string(xml_string.encode('utf-8'))
            self.assertTrue(cm.output[0].startswith('WARNING'))


if __name__ == '__main__':
    unittest2.main()
