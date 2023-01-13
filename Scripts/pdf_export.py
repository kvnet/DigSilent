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
from dataclasses import dataclass
from PyPDF2 import PdfWriter, PdfReader

# Powerfactory-Objekte festlegen
app = powerfactory.GetApplication() # Application-Objekt
script = app.GetCurrentScript() # Aktives Powerfactory-Skript-Objekt

# Export-Eigenschaften festlegen
filetype = 'emf' # Dateiendung festlegen (!!! OHNE PUNKT !!!)
iopt_savas = 0  # 0=Datei im angegebenen Pfad des Filenamens speichern, 1=Ruft den 'Speichern Unter...'-Dialog auf
iRange = 0 # Exportbereich: 0 = Gesamtes Diagramm, 1 = Gesamtes Diagramm mit aktuellen Zoomeinstellungen, 2 = Sichtbarer Bereich 
dpi = 1000 # Auflösung der Ausgabe in DPI 
iFrame = True # Rahmen erzeugen

# PDF-Eigenschaften
ptmm_converter = float(0.3527777778) # Umrechnungsfaktor Punkt zu 'mm'

# KLASSEN
# Enumerator für PowerFactory Klassen-Typen
class PfClsType:
        SetDeskpage = '*.SetDeskpage'
        SetFormat = '*.SetFormat'
        SetGrfpage = '*.SetGrfpage'
        

#@dataclass(frozen=True)
class Deskpage:
        page: object
        path: str
        calculation_type: str
        file_extension: str
        datesuffix: bool

        def __init__(self, page, path, ctype, file_extension, datesuffix = False) -> None:
                self.page = page
                self.path = path
                self.ctype = ctype
                self.file_extension = file_extension
                self.datesuffix = datesuffix
                self.file_export: bool = False
                self.file_formation: bool = False
                self.__pgname: str = page.GetAttribute('loc_name') # Name des Objektes in der Grafiksammlung
                self.__pgorder: str = str(page.GetAttribute('order')) # Seitennummer (= Reihenfolge in der Grafiksammlung -> immer eine Zahl in PF)

        # Dateiname ohne Erweiterung
        @property
        def filename(self) -> str:
                # Rückgabe des Dateinamens (ohne Verzeichnis)
                return f'{self.ctype}_{self.page_number}_{self.__pgname}{self.__datesuffix()}.{self.file_extension}'
                
        # vollständiger Dateinamens inkl. Pfad
        @property
        def fullfilename(self)-> str:
                return os.path.join(self.path, self.filename)

        # Seitennummer
        @property
        def page_number(self) -> str:
                # umwandeln der Seitennummer 3-stellig mit führenden Nullen
                return self.__pgorder.zfill(3)

        # Seitenformat-Name der aktiven Grafik
        @property
        def page_format_name(self) -> str:
            setgrphpg = self.__getgrphpg()  
            return setgrphpg.GetAttribute('aDrwFrm')

        def __datesuffix(self) -> str:
                if (self.__datesuffix == True):
                        date = dt.datetime.now().strftime('%Y%m%d')
                        return '_' + date
                return ''

        def __getgrphpg(self) -> object:
            diag = self.page.GetAttribute('pGrph')
            setgrphpgs = diag.GetChildren(1, PfClsType.SetGrfpage, 1)
            return setgrphpgs[0]


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

        # Seitenformate aus den Powerfactory-Projekteinstellungen in Dictionary Speichern
        # Projekt\Einstellungen\Page Formats
        pageformats = ProjectPageFormats(script.PageFormats, PfClsType.SetFormat)

        # ---> '############### STARTE EXPORT: ###############'
        # Informationsausgabe in PowerFactory
        strInfoHeader = f' STARTE {filetype.upper()}-EXPORT: '
        app.PrintInfo(strInfoHeader.center(50, '#'))

        # Inhalt des GraphicsBoard-Objektes in neue Liste 'deskpages' laden
        graphicboards=desktop.GetContents(PfClsType.SetDeskpage)
        deskpages = GetDeskpageList(graphicboards, exportpath, prefixtuple[calctypeindex], setdatesuffix)

        exportssuccess = 0
        exportsfailure = 0
        for dpg in deskpages:
                p = dpg.page
                pname = p.GetAttribute('loc_name') # oder auch nur deskpage.loc_name falls Attribut bekannt
                ffname = dpg.fullfilename

                app.PrintPlain(f'Exportiere Deskpage {pname}') # nach {ffname}')

                if file_exists(ffname) == True:
                        if delete_file(ffname) == False: #Wenn die Datei nicht gelöscht werden kann, Fehlermeldung ausgeben
                                dpg.file_export = False
                                #exportsfailure += 1

                
                if desktop.Show(p) == 0: # Grafik aufrufen und anzeigen
                        app.SetGraphicUpdate(1)        
                        app.SetGuiUpdateEnabled(1)

                        if ExportDeskpage(dpg) == True:
                                dpg.file_export = True
                                if SetupPdfPage(dpg, pageformats) == True:
                                        dpg.file_formation = True
                        

                                
                                #exportssuccess += 1                  

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
# einer 'Deskpage'-Klasse übergeben und selbige in einer Liste speichern
def GetDeskpageList(graphicboards: object, exportpath: str, calctype: str, setdatesuffix: bool):
        graphicboardlist = [] # Leere Liste für Deskpage-Klassen erstellen
        for graphicboard in graphicboards:
                # Eigenschaft 'Seite wiederverwerten' der Grafikseite auslesen und als Ausgabe-Option verwenden
                pgexport = bool(graphicboard.iRecycl) # oder auch anders geschrieben: deskpage.GetAttribute('iRecycl')
                if pgexport == True:
                        deskpageclass = Deskpage(graphicboard,
                                                exportpath,
                                                calctype,
                                                filetype,
                                                setdatesuffix)
                        graphicboardlist.append(deskpageclass)
        return graphicboardlist

# Export der Netzgraphik
def ExportDeskpage(deskpageclass: Deskpage) -> bool:
        try:
                # QUELLE: https://www.digsilent.de/en/faq-reader-powerfactory/how-do-i-export-a-graphic-using-python.html
                # Aufruf des CommonWrite-Objektes von Powerfactory
                comWr = app.GetFromStudyCase('ComWr')
                comWr.SetAttribute('iopt_rd', filetype)
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
def SetupPdfPage(deskpageclass: Deskpage, pageformats: dict) -> bool:
        # Prüfen, ob der Name des in der Klasse gespeicherten Seitenformats
        # im Dictionary enthalten ist
        key = deskpageclass.page_format_name
        if key in pageformats:
                try:
                        # Lesen der existierenden PDF-Datei
                        pdf = PdfReader(deskpageclass.fullfilename)
                        # Ermitteln der PDF-Dimensionen (Breite/Höhe)
                        pdfpage = pdf.pages[0] # 1. Seite laden
                        source_width, source_height = pdfpage.mediabox.upper_right # Ermitteln der Breite und Höhe in Punkten
                        source_height = float(source_height) * ptmm_converter # Umrechnen der ermittelten Höhe in [mm]

                        # Skalieren der PDF-Datei auf die neue Zielhöhe
                        target_width, target_height = pageformats[key]
                        scale = ScaleFactor(source_height, target_height)
                        #app.PrintPlain(f'{key} Breite: {source_width}, Höhe: {source_height} => Breite: {target_width}, Höhe: {target_height} Skalierung: {scale}') # TEST
                        
                        pdfpage.scale_by(scale)

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
        else:        
                return False


# Berechnet den Skalierungsfaktor anhand der alten Höhe in [mm] zur neuen Höhe in [mm]
def ScaleFactor(source_height, target_height) -> int:
        return target_height/source_height

# Auslesen aller in den Projekteinstellungen vorhandenen Seitenformate
# Rückgabe eines Dictionary {'Seitenformatname':[Breite, Höhe]}
def ProjectPageFormats(ext_script_obj, contenttype: str) -> dict:
        pageformats = {} # Leeres Dictionary
        prjpageformats = ext_script_obj.GetContents(contenttype)
        
        # Alle Seitenformate durchlaufen, Werte auslesen und
        # als Dictionary zurückgeben
        for pgformat in prjpageformats:
                fname = pgformat.GetAttribute('loc_name') # Namen auslesen
                f_width = pgformat.GetAttribute('iSizeX') # Seitenbreite auslesen
                f_height = pgformat.GetAttribute('iSizeY') # Seitenhöhe auslesen
                
                pageformats[fname] = [f_width, f_height]

        return pageformats

def file_exists(fullfilename) -> bool:
        return os.path.isfile(fullfilename)

def delete_file(fullfilename) -> bool:
        try: # Versuche die vorhandenen Datei zu löschen
                os.remove(fullfilename)
                return True
        except: #Wenn die Datei nicht gelöscht werden kann, Fehlermeldung ausgeben
                app.PrintWarn(f'Export fehlgeschlagen: {fullfilename}')
                return False


# Einstiegspunkt
if __name__ == '__main__':
        # Grafiksammlung des aktiven Berechnungsfalles in Objekt laden
        desktop = app.GetGraphicsBoard()
        # Wenn Desktop-Objekt (aktives GraphicsBoard) leer ist, dann Skript verlassen
        if not (desktop):
                exit()
        # Grafiksammlung an die Hauptfunktion übergeben und ausführen
        main(desktop)

