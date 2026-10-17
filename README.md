# Gruenbeck softliQ für Home Assistant

Diese Custom Integration fragt `http://<IP-Adresse>/mux_http` ab und stellt die gelieferten Werte als Sensoren bereit. Die Anlage wird standardmäßig einmal pro Minute abgefragt. Da die Weboberfläche langsam antworten kann, hat jede Anfrage ein Zeitlimit von 45 Sekunden; fehlgeschlagene Abfragen behalten die letzten Sensorwerte bei und werden durch Home Assistant erneut versucht.

## Installation

Den Ordner `custom_components/gruenbeck_softliq` in das Verzeichnis `custom_components` deiner Home-Assistant-Konfiguration kopieren und Home Assistant neu starten. Anschließend unter **Einstellungen > Geräte & Dienste > Integration hinzufügen** nach **Grünbeck softliQ** suchen und die IP-Adresse eingeben.

Die IP-Adresse kann später in den Optionen der Integration geändert werden. Diagnoseinformationen einschließlich des Zeitpunkts des letzten erfolgreichen Abrufs sind über **Geräte & Dienste > Grünbeck softliQ > Diagnose herunterladen** verfügbar.

Nicht von der Anlage gelieferte Werte wie Wartungsintervall oder Salzreichweite werden als nicht verfügbar angezeigt, nicht als erfundene Nullwerte. Der Regenerationsschritt-Restwert hat keine festgelegte Einheit, da die Anlage dort je nach Zustand Dauer oder Menge liefern kann.