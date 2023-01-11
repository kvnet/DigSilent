# DigSilent Version 2019
# Python (!!!) Version 3.7 (!!!) muss installiert sein
# Copyright 2022 Christian Vavru

# Dependencies
# pip install PyPDF2
# oder
# pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org PyPDF2
# https://jhooq.com/pip-install-connection-error/

import powerfactory # Importieren des DigSilent Powerfactory Moduls
import os
import datetime as dt
from PyPDF2 import PdfWriter, PdfReader

# Powerfactory-Objekte festlegen
app = powerfactory.GetApplication() # Application-Objekt
script = app.GetCurrentScript() # Aktives Powerfactory-Skript-Objekt

# Export-Eigenschaften festlegen
exportfiletype = 'pdf' # Dateiendung festlegen (!!! OHNE PUNKT !!!)
iopt_savas = 0  # 0=Datei im angegebenen Pfad des Filenamens speichern, 1=Ruft den 'Speichern Unter...'-Dialog auf
iRange = 0 # Exportbereich: 0 = Gesamtes Diagramm, 1 = Gesamtes Diagramm mit aktuellen Zoomeinstellungen, 2 = Sichtbarer Bereich 
dpi = 1000 # Auflösung der Ausgabe in DPI 
iFrame = True # Rahmen erzeugen

# PDF-Eigenschaften
ptmm_converter = float(0.3527777778) # Umrechnungsfaktor Punkt zu 'mm'

# KLASSEN
class ExportDeskPage:
        
        # Konstruktor
        def  __init__(self, page:object, exportpath:str, calctype:str, filetype:str, setdatesuffix=False):
                self.page = page # Page-Objekt von Powerfactory
                self.exportpath = str(exportpath) # ExportPath-Eingabe des Skripts als String
                self.calctype = calctype # Kalklulationsart-Kürzel von prefixtuple als String
                self.setdatesuffix = setdatesuffix # Boolean, ob Datumskürzel hinzugefügt wird
                self.filetype = filetype # Datei-Endung als String

        # Dateiname ohne Erweiterung
        @property
        def filename(self):
                # Rückgabe des Dateinamens (ohne Verzeichnis)
                fn = f'{self.calctype}_{self.page_number}_{self.page.loc_name}{self.__datesuffix()}.{self.filetype}'
                return fn
                
        # vollständiger Dateinamens inkl. Pfad
        @property
        def fullfilename(self):
                return os.path.join(self.exportpath, self.filename)

        # Seitennummer
        @property
        def page_number(self):
                # Seitennummer aus dem Page-Objekt auslesen
                # (= Reihenfolge in der Grafiksammlung ist in Powerfactory immer eine Zahl)
                pgnr = int(self.page.order) # oder auch anders geschrieben: page.GetAttribute('order')
                # umwandeln der Seitennummer 3-stellig mit führenden Nullen
                return str(pgnr).zfill(3)

        # Seitenformat-Name der aktiven Grafik
        @property
        def page_format_name(self):
            setgrphpg = self.__getgrphpg  
            return setgrphpg.GetAttribute('aDrwFrm')

        # Seitenausrichtung der aktiven Grafik (0=Hochformat, 1=Querformat)
        @property
        def page_orientation(self):
            setgrphpg = self.__getgrphpg
            orientation = int(setgrphpg.GetAttribute('iDrwFrm'))
            return orientation

        # Rückgabe des Seitenabmessungen der aktiven Grafik
        # def _page_dimensions(self):
        #     aDrwFrm = self._page_formatname()
        #     width = aDrwFrm.GetAttribute('iSizeX')
        #     height = aDrwFrm.GetAttribute('iSizeY')
        #     return (width, height)

        def __datesuffix(self):
                if (self.__datesuffix == True):
                        date = dt.datetime.now().strftime('%Y%m%d')
                        return '_' + date
                return ''

        def __getgrphpg(self):
            diag = self.page.GetAttribute('pGrph')
            setgrphpgs = diag.GetChildren(1, 'Format.SetGrfpage', 1)
            return setgrphpgs[0]

        def file_exists(self):
            return os.path.isfile(self.fullfilename)

        def delete_file(self):
            ffname = self.fullfilename
            try: # Versuche die vorhandenen Datei zu löschen
                os.remove(ffname)
            except: #Wenn die Datei nicht gelöscht werden kann, Fehlermeldung ausgeben
                app.PrintWarn(f'Export fehlgeschlagen: {ffname}')
                return False
            return True


# FUNKTIONEN / DEFINITITIONEN
def main(desktop):
        prefixtuple = ('Base', 'Ldfl', 'Shc3', 'Shc1') # Tuple-Collection der Präfixe
        errormsgs = [] # Leere Liste für Fehlermeldungen erstellen

        # Skript-Eingabedaten überprüfen

        # Überprüfen ob der im Skript angegebene Pfad existiert
        exportpath = CheckExportPath(str(script.ExportPath))
        if exportpath == '':
                errormsgs.append('Fehlender oder falscher Exportpfad! Skript-Abbruch!')

        # Überprüfen der Berechnungsart
        calctypeindex = int(script.CalcType)
        if CalcTypeIndexInRange(calctypeindex, prefixtuple) == False:
                errormsgs.append('Die Variable CalcType liegt ausserhalb ' + \
                        'des gültigen Bereiches (0-3)! Skript-Abbruch!')

        # Überprüfen ob Datum als Datei-Suffix hinzugefügt werden soll
        setdatesuffix = SetScriptDateSuffix(int(script.DateSuffix))
       
        # Überprüfen, ob ein Unterverzeichnis angegeben wurde
        if (str(script.SubDir) != ''):
                exportpath = os.path.join(exportpath, str(script.SubDir))

        # Wenn Fehlermeldungen in der Liste errormsgs vorhanden sind,
        # dann selbige anzeigen und Skript beenden
        if len(errormsgs) > 0:
                for errmsg in errormsgs:
                        app.PrintError(errmsg)
                exit()



        # ---> '############### STARTE EXPORT: ###############'
        # Informationsausgabe in PowerFactory
        strInfoHeader = f' STARTE {exportfiletype.upper()}-EXPORT: '
        app.PrintInfo(strInfoHeader.center(50, '#'))

        # Inhalt des GraphicsBoard-Objektes in neue Liste 'deskpages' laden
        graphicboards=desktop.GetContents()
        deskpages = GetDeskpageList(graphicboards, exportpath, prefixtuple[calctypeindex], setdatesuffix)

        exportssuccess = 0
        exportsfailure = 0
        for deskpageclass in deskpages:
                # Überprüfen, ob deskpage eine Klasseninstanz von ExportDeskPage ist
                if isinstance(deskpageclass, ExportDeskPage) == True:
                        p = deskpageclass.page
                        pname = p.GetAttribute('loc_name') # oder auch nur deskpage.loc_name falls Attribut bekannt
                        ffname = deskpageclass.fullfilename

                        app.PrintPlain(f'Exportiere Grafik {pname}') # nach {ffname}')

                        if deskpageclass.file_exists() == True:
                                if deskpageclass.delete_file() == False: #Wenn die Datei nicht gelöscht werden kann, Fehlermeldung ausgeben
                                        exportsfailure += 1

                        
                        #if desktop.Show(p) == 0: # Grafik aufrufen und anzeigen
                                #app.SetGraphicUpdate(1)
                                #app.SetGuiUpdateEnabled(1)

                        export = ExportDeskpage(deskpageclass)
                        #scale = SetupPdfPage(deskpageclass)
                        scale = True
                        if export == True and scale == True:
                               exportssuccess += 1                  

        info_str = f'Erfolgreiche Exporte: {exportssuccess}, Fehlgeschlagene Exporte: {exportsfailure}'
        
        if exportsfailure > 0:
                app.PrintWarn(info_str) # Bei fehlgeschlagenen Exporten, Warnmeldung ausgeben
        else:
                app.PrintInfo(info_str) # anderenfalls, Information ausgeben


# Prüfung der Benutzereingabe der Variable 'ExportPath'
def CheckExportPath(targetpath: str):
        # Wenn angegebener Pfad ungültig oder nicht vorhanden ist, ...
        if os.path.exists(targetpath) == False or targetpath == '':
                # Leeren String zurück geben
                return ''
        else:
                # übergebenen Pfad als String zurück geben
                return targetpath

# Prüfung der Benutzereingabe der Variable 'CalcType'
def CalcTypeIndexInRange(calctypeindex, prefixtuple):
        # Wenn die Benutzereingabe der Variable 'CalcType'
        # außerhalb des Bereiches 0-3 liegt, wird 'Falsch' zurück gegeben
        if calctypeindex in range(0, len(prefixtuple)):
                return True
        else:
                return False

def SetScriptDateSuffix(datesuffix):
        # Wenn die Benutzereingabe der Variable 'DateSuffix' nicht 1 ist
        # wird selbige auf 0 gesetzt und eine Warnmeldung ausgegeben
        if (datesuffix != 0 and datesuffix != 1):
                script.SetInputParameterInt('DateSuffix', 0)
                app.PrintWarn('Falsche Eingabe für das DateSuffix! ' + \
                        'Wert wurde auf 0 zurückgesetzt!')
        return bool(script.DateSuffix) # Wahrheitswert zurück geben

# Alle Netzgrafiken der Grafiksammlung des aktiven Berechnungsfalles durchlaufen,
# einer 'ExportDeskPage'-Klasse übergeben und selbige in einer Liste speichern
def GetDeskpageList(graphicboards: object, exportpath: str, calctype: str, setdatesuffix: bool):
        graphicboardlist = [] # Leere Liste für ExportDeskPage-Klassen erstellen
        for graphicboard in graphicboards:
                # Eigenschaft 'Seite wiederverwerten' der Grafikseite auslesen und als Ausgabe-Option verwenden
                pgexport = bool(graphicboard.iRecycl) # oder auch anders geschrieben: deskpage.GetAttribute('iRecycl')
                if pgexport == True:
                        deskpageclass = ExportDeskPage(graphicboard, exportpath, calctype, exportfiletype, setdatesuffix)
                        graphicboardlist.append(deskpageclass)
        return graphicboardlist

# Export der Netzgraphik
def ExportDeskpage(deskpageclass: ExportDeskPage):
        try:
                # QUELLE: https://www.digsilent.de/en/faq-reader-powerfactory/how-do-i-export-a-graphic-using-python.html
                # Aufruf des CommonWrite-Objektes von Powerfactory
                comWr = app.GetFromStudyCase('ComWr')
                comWr.SetAttribute('iopt_rd', exportfiletype)
                #comWr.iopt_nonly = 0  # to write a file
                comWr.SetAttribute('iopt_savas', iopt_savas)
                comWr.SetAttribute('f', deskpageclass.fullfilename) # Filename
                comWr.iRange = iRange
                comWr.iFrame = iFrame
                comWr.dpi = dpi # Auflösung der Ausgabe in DPI
                comWr.Execute()
                return True
        except:
                return False

# Skaliert die Seite der exportierten PDF-Datei und fügt Meta-Daten hinzu
def SetupPdfPage(deskpageclass: ExportDeskPage):
        try:
                # Lesen der existierenden PDF-Datei
                pdf = PdfReader(deskpageclass.fullfilename)
                # Ermitteln der PDF-Dimensionen (Breite/Höhe)
                pdfpage = pdf.pages[0] # 1. Seite laden
                source_width, source_height = pdfpage.mediabox.upper_right # Ermitteln der Breite und Höhe in Punkten
                source_height = float(source_height) * ptmm_converter # Umrechnen der ermittelten Höhe in [mm]

                # Skalieren der PDF-Datei auf die neue Zielhöhe
                target_width, target_height = deskpageclass._page_dimensions()
                pdfpage.scale_by(ScaleFactor(source_height, target_height))

                new_pdfpage = PdfWriter()
                new_pdfpage.add_page(pdfpage)
                
                # Metadaten hinzufügen
                username = app.GetSettings('username')
                title = f'{deskpageclass.calctype} {deskpageclass.page.loc_name}'
                new_pdfpage.add_metadata(
                        {
                        "/Title": title,
                        "/Author": username,
                        "/Producer": "DIgSILENT Powerfactory 2019"
                        }
                )

                # Ausgabe der neuen PDF-Datei -> die Original-Datei wird überschrieben
                new_pdfpage.write(pdf)
                return True
        except:

                return False

# Berechnet den Skalierungsfaktor anhand der alten Höhe in [mm] zur neuen Höhe in [mm]
def ScaleFactor(source_height, target_height):
        return target_height/source_height

# Einstiegspunkt
if __name__ == '__main__':
        # Grafiksammlung des aktiven Berechnungsfalles in Objekt laden
        desktop = app.GetGraphicsBoard()
        # Wenn Desktop-Objekt (aktives GraphicsBoard) leer ist, dann Skript verlassen
        if not (desktop):
                exit()
        # Grafiksammlung an die Hauptfunktion übergeben und ausführen
        main(desktop)

