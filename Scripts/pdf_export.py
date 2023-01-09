# DigSilent Version 2019
# Python (!!!) Version 3.7 (!!!) muss installiert sein
# Copyright 2019 Christian Vavru

import powerfactory # Importieren des DigSilent Powerfactory Moduls
import os
import datetime as dt

# Powerfactory-Objekte festlegen
app = powerfactory.GetApplication() # Application-Objekt
script = app.GetCurrentScript() # Aktives Powerfactory-Skript-Objekt

# Export-Eigenschaften festlegen
exportfiletype = 'pdf' # Dateiendung festlegen (!!! OHNE PUNKT !!!)
iopt_savas = 0  # 0=Datei im angegebenen Pfad des Filenamens speichern, 1=Ruft den 'Speichern Unter...'-Dialog auf
iRange = 0 # Exportbereich: 0 = Gesamtes Diagramm, 1 = Gesamtes Diagramm mit aktuellen Zoomeinstellungen, 2 = Sichtbarer Bereich 
dpi = 1000 # Auflösung der Ausgabe in DPI 
iFrame = True # Rahmen erzeugen

# KLASSEN
class ExportPage:
        # Konstruktor
        def  __init__(self, page: object, path: str, calctype: str, filetype: str, setdatesuffix=False):
                self.page = page # Page-Objekt von Powerfactory
                self._path = path # ExportPath-Eingabe des Skripts
                self._calctype = calctype
                self._setdatesuffix = setdatesuffix
                self._filetype = filetype

        # Eigenschaft zur Rückgabe des Dateinamens ohne Erweiterung
        @property
        def filename(self):
                # Rückgabe des Dateinamens (ohne Verzeichnis)
                return self._calctype + '_' + \
                        self.pagenumber + '_' + \
                        self.page.loc_name + \
                        self.datesuffix + \
                        '.' + self._filetype            

        @property
        def datesuffix(self):
                if (self.datesuffix == True):
                        date = dt.datetime.now().strftime('%Y%m%d')
                        return '_' + date
                return ''

        @property
        def pagenumber(self):
                # Seitennummer aus dem Page-Objekt auslesen
                # (= Reihenfolge in der Grafiksammlung ist in Powerfactory immer eine Zahl)
                pgnr = int(self.page.order) # oder auch anders geschrieben: page.GetAttribute('order')
                # umwandeln der Seitennummer 3-stellig mit führenden Nullen
                return str(pgnr).zfill(3)

        # Rückgabe des Seitenformates der aktiven Grafik
        @property
        def pageformat_name(self):
            diag = self.page.GetAttribute('pGrph')
            setgrphpgs = diag.GetChildren(1, 'Format.SetGrfpage', 1)
            setgrphpg = setgrphpgs[0]
            return setgrphpg.GetAttribute('aDrwFrm')           

        # Rückgabe des vollständigen Dateinamens inkl. Pfad
        @property
        def fullfilename(self):
                return os.path.join(self._path, self.filename)


        def file_exists(self):
            return os.path.isfile(self.fullfilename)

        def delete_file(self):
            ffn = self.fullfilename
            try: # Versuche die vorhandenen Datei zu löschen
                os.remove(ffn)
            except: #Wenn die Datei nicht gelöscht werden kann, Fehlermeldung ausgeben
                app.PrintWarn('Export fehlgeschlagen: ' + str(ffn))
                return False
            return True

        def ExportGraph():
                pass


# FUNKTIONEN / DEFINITITIONEN
def main(desktop):
        prefixtuple = ('Base', 'Ldfl', 'Shc3', 'Shc1') # Tuple-Collection der Präfixe
        graphs = [] # Leere Liste für ExportPage-Klassen erstellen
        errormsgs = [] # Leere Liste für Fehlermeldungen erstellen

        # Informationsausgabe in PowerFactory
        strInfoHeader = ' STARTE ' + exportfiletype.upper() + '-EXPORT: '
        app.PrintInfo(strInfoHeader.center(50, '#'))

        # ---> '############### STARTE EXPORT: ###############'

        # 1.) Überprüfen ob der im Skript angegebene Pfad existiert
        exportpath = CheckExportPath(str(script.ExportPath))
        if exportpath == '':
                errormsgs.append('Fehlender oder falscher Exportpfad! Skript-Abbruch!')

        # 2.) Überprüfen der Berechnungsart
        calctypeindex = int(script.CalcType)
        if CheckCalctype(calctypeindex) == False:
                errormsgs.append('Die Variable CalcType liegt ausserhalb ' + \
                        'des gültigen Bereiches (0-3)! Skript-Abbruch!')
        else:
                calctypeindex = int(script.CalcType)

        # 3.) Überprüfen ob Datum als Datei-Suffix hinzugefügt werden soll
        setdatesuffix = CheckScriptDateSuffix(int(script.DateSuffix))

        # 4.) Überprüfen ob Fehlermeldungen in der Liste errormsgs vorhanden sind
        # Wenn Ja, dann Fehlermeldungen anzeigen und Skript beenden
        if len(errormsgs) > 0:
                for errmsg in errormsgs:
                        app.PrintError(errmsg)
                exit()
        
        # 5.) Überprüfen, ob ein Unterverzeichnis angegeben wurde
        if (str(script.SubDir) != ''):
                exportpath = os.path.join(exportpath, str(script.SubDir))

        # Inhalt des GraphicsBoard-Objektes in neue Liste 'pages' laden
        pages = desktop.GetContents()
        # Alle in der Grafiksammlung vorhandenen Netzgrafiken durchlaufen,
        # an Klasse 'ExportPage' übergeben und die Klassen in einer Liste
        # speichern 
        for page in pages:
                # Eigenschaft 'Seite wiederverwerten' der Grafikseite auslesen und als Ausgabe-Option verwenden
                pgexport = bool(page.iRecycl) # oder auch anders geschrieben: page.GetAttribute('iRecycl')
                if pgexport == True:
                        epg = ExportPage(page, exportpath, prefixtuple[calctypeindex], exportfiletype, setdatesuffix)
                        graphs.append(epg)


        exportssuccess = 0
        exportsfailure = 0
        for graph in graphs:
                p = graph.page
                pn = p.GetAttribute('loc_name') # oder auch nur page.loc_name falls Attribut bekannt
                ffn = graph.fullfilename

                app.PrintPlain('Exportiere Grafik ' + pn)
                app.PrintPlain('Exportiere Grafik nach ' + ffn)

                # if graph.file_exists() == True:
                #         if graph.delete_file() == False: #Wenn die Datei nicht gelöscht werden kann, Fehlermeldung ausgeben
                #                 exportsfailure += 1

                
                #if desktop.Show(p) == 0: # Grafik aufrufen und anzeigen
                        #app.SetGraphicUpdate(1)
                       # app.SetGuiUpdateEnabled(1)

                # QUELLE: https://www.digsilent.de/en/faq-reader-powerfactory/how-do-i-export-a-graphic-using-python.html
                # Aufruf des CommonWrite-Objektes von Powerfactory
                # comWr = app.GetFromStudyCase('ComWr')
                # comWr.SetAttribute('iopt_rd', exportfiletype)
                # #comWr.iopt_nonly = 0  # to write a file
                # comWr.SetAttribute('iopt_savas', iopt_savas)
                # comWr.SetAttribute('f', str(ffn)) # Filename
                # comWr.iRange = iRange
                # comWr.iFrame = iFrame
                # comWr.dpi = dpi # Auflösung der Ausgabe in DPI
                # comWr.Execute()

                exportssuccess += 1

        if exportsfailure > 0:
                app.PrintWarn('Erfolgreiche Exporte: ' + str(exportssuccess) + \
                        ', Fehlgeschlagene Exporte: ' + str(exportsfailure))
        else:
                app.PrintInfo('Erfolgreiche Exporte: ' + str(exportssuccess) + \
                        ', Fehlgeschlagene Exporte: ' + str(exportsfailure))


def CheckExportPath(strPath):
        # Wenn angegebener Pfad ungültig oder nicht vorhanden ist, ...
        if os.path.exists(strPath) == False or strPath == '':
                # Leeren String zurück geben
                return ''
        else:
                # übergebenen Pfad als String zurück geben
                return strPath


def CheckCalctype(intCalctype):
        # Wenn die Benutzereingabe der Variable 'CalcType'
        # außerhalb des Bereiches 0-3 liegt, wird 'Falsch' zurück gegeben
        if intCalctype in range(0, 4):
                return True
        else:
                return False


def CheckScriptDateSuffix(intDatesuffix):
        # Wenn die Benutzereingabe der Variable 'DateSuffix' nicht 1 ist
        # wird selbige auf 0 gesetzt und eine Warnmeldung ausgegeben
        if (intDatesuffix != 0 and intDatesuffix != 1):
                script.SetInputParameterInt('DateSuffix', 0)
                app.PrintWarn('Falsche Eingabe für das DateSuffix! ' + \
                        'Wert wurde auf 0 zurückgesetzt!')
        return bool(script.DateSuffix) # Wahrheitswert zurück geben


#Einstiegspunkt
if __name__ == '__main__':

        # Grafiksammlung des aktiven Berechnungsfalles in Objekt laden
        desktop = app.GetGraphicsBoard()
        # Wenn Desktop-Objekt (aktives GraphicsBoard) leer ist, dann Skript verlassen
        if not (desktop):
                exit()
        # Grafiksammlung an die Hauptfunktion übergeben
        main(desktop)

