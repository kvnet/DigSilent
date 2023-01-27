# DigSilent Version 2019
# Python (!!!) Version 3.7 (!!!) muss installiert sein
# Copyright 2023 Christian Vavru

# ********* SKRIPT-GRUND-OPTIONEN *********
# Eingabeparameter
# Typ       Name            Wert    Beschreibung 
# string    Path                    Zielverzeichnis für die zu exportierenden Grafiken
# string    Subpath                 Unterverzeichnis
# int       PgFormgSubDir	0		Unterverzeichnis gem. Seitenformat erstellen: 0=Nein; 1=Ja
# string    CalcPrefix              Berechnungsart (z.B. Base, Ldfl, Shc1, Shc3)
# int       SetPageNumber	1		Seitennummer gem. Reihenfolge in der aktiven Grafiksammlung hinzu
# int       DateSuffix      1		Datum als Dateiendung hinzu (0 oder Leer=Nein, 1=Ja)

# Externe Objekte:
# Name          Objekt                                          Beschreibung
# PageFormats	\Einstellungen.SetFold\Page Formats.SetFoldpage	Settings der Seitenformate (.SetFoldpage)

# Modulimporte
import powerfactory # Importieren des DigSilent Powerfactory Moduls
import os
import datetime as dt
from enum import Enum
from dataclasses import dataclass

# Powerfactory-Objekte
app = powerfactory.GetApplication() # Application-Objekt
script = app.GetCurrentScript() # Aktives Powerfactory-Skript-Objekt
# Zulässige Dateitypen
extensions = ("bmp", "emf", "gif", "jpeg", "pdf", "svg", "tiff", "wmf")

# Enumerator für PowerFactory Klassen-Typen
class PfClassType(Enum):
        SETDESKPAGE = '*.SetDeskpage'
        SETFORMAT = '*.SetFormat'
        SETGRFPAGE = '*.SetGrfpage'

@dataclass
class Graph:
    """Grafik-Objekt für den Export von Powerfactory in das gewünschte Format"""
    pass

@dataclass (frozen=True)
class ScriptDataValidator:
        """Klasse zur Überprüfung der Eingabeparameter und externen Objekte des Skriptes """
        script: object


# FUNKTIONEN / DEFINITITIONEN
def main(desktop):
    errormsgs = [] # Leere Liste für Fehlermeldungen erstellen

    # Skript-Eingabedaten überprüfen
    scriptdata = ScriptDataValidator(script)

    # Seitenformate aus den Powerfactory-Projekteinstellungen in Dictionary Speichern
    # Projekt\Einstellungen\Page Formats
    pageformats = ProjectPageFormats(script.PageFormats, PfClassType.SETFORMAT)


def ProjectPageFormats(ext_script_obj, contenttype: str) -> dict:
    """Funktion zum Auslesen aller in den Projekteinstellungen vorhandenen Seitenformate
    Rückgabe eines Dictionary {'Seitenformatname':[Breite, Höhe]}"""
    pageformats = {} # Leeres Dictionary
    prjpageformats = ext_script_obj.GetContents(contenttype)
        
    # Alle Seitenformate durchlaufen, Werte auslesen und als Dictionary zurückgeben
    for pgformat in prjpageformats:
        fname = pgformat.GetAttribute('loc_name') # Namen auslesen
        f_width = pgformat.GetAttribute('iSizeX') # Seitenbreite auslesen
        f_height = pgformat.GetAttribute('iSizeY') # Seitenhöhe auslesen
                
        pageformats[fname] = [f_width, f_height]

    return pageformats


def ExportDeskpage(exportgraph: Graph) -> bool:
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


# Einstiegspunkt
if __name__ == '__main__':
    # Grafiksammlung des aktiven Berechnungsfalles in Objekt laden
    desktop = app.GetGraphicsBoard()
    # Wenn Desktop-Objekt (aktives GraphicsBoard) leer ist, dann Skript verlassen
    if not (desktop):
        exit()
    main(desktop) # Hauptfunktion aufrufen und Grafiksammlung übergeben