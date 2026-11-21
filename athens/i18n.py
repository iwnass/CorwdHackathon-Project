"""Labels for the codes the API returns, in 9 languages. The API itself always returns stable codes
("busy", "museum", "caution"…); the app looks them up here once (GET /api/i18n?lang=…).

shortcut: written by hand, not by native speakers — have each language reviewed before a public launch.
"""
LANGS = ("en", "el", "de", "fr", "es", "ru", "zh", "ja", "ar")
RTL = {"ar"}

# code → "en|el|de|fr|es|ru|zh|ja|ar"
_TABLE = {
    # place kinds
    "museum": "Museum|Μουσείο|Museum|Musée|Museo|Музей|博物馆|博物館|متحف",
    "gallery": "Art gallery|Πινακοθήκη|Kunstgalerie|Galerie d'art|Galería de arte|Художественная галерея|美术馆|美術館|معرض فني",
    "library": "Library|Βιβλιοθήκη|Bibliothek|Bibliothèque|Biblioteca|Библиотека|图书馆|図書館|مكتبة",
    "theatre": "Theatre|Θέατρο|Theater|Théâtre|Teatro|Театр|剧院|劇場|مسرح",
    "cultural_centre": "Cultural centre|Πολιτιστικό κέντρο|Kulturzentrum|Centre culturel|Centro cultural|Культурный центр|文化中心|文化センター|مركز ثقافي",
    "cinema": "Cinema|Κινηματογράφος|Kino|Cinéma|Cine|Кинотеатр|电影院|映画館|سينما",
    "place": "Place|Τοποθεσία|Ort|Lieu|Lugar|Место|地点|地名|مكان",
    "metro_station": "Metro station|Σταθμός μετρό|U-Bahn-Station|Station de métro|Estación de metro|Станция метро|地铁站|地下鉄駅|محطة مترو",
    "tram_stop": "Tram stop|Στάση τραμ|Straßenbahnhaltestelle|Arrêt de tramway|Parada de tranvía|Трамвайная остановка|有轨电车站|路面電車停留所|محطة ترام",
    "rail_station": "Railway station|Σιδηροδρομικός σταθμός|Bahnhof|Gare|Estación de tren|Железнодорожная станция|火车站|鉄道駅|محطة قطار",
    "free_wifi": "Free Wi-Fi|Δωρεάν Wi-Fi|Kostenloses WLAN|Wi-Fi gratuit|Wi-Fi gratis|Бесплатный Wi-Fi|免费无线网络|無料Wi-Fi|واي فاي مجاني",
    "accessible_parking": "Accessible parking|Θέση στάθμευσης ΑμεΑ|Behindertenparkplatz|Place de stationnement PMR|Aparcamiento accesible|Парковка для людей с инвалидностью|无障碍停车位|障害者用駐車場|موقف لذوي الإعاقة",
    "fountain": "Drinking fountain|Βρύση πόσιμου νερού|Trinkbrunnen|Fontaine d'eau potable|Fuente de agua potable|Питьевой фонтанчик|饮水点|水飲み場|نافورة مياه شرب",
    "pocket_park": "Pocket park|Πάρκο τσέπης|Kleiner Park|Mini-parc|Parque de bolsillo|Мини-парк|口袋公园|ポケットパーク|حديقة صغيرة",
    "pool": "Swimming pool|Κολυμβητήριο|Schwimmbad|Piscine|Piscina|Бассейн|游泳池|プール|مسبح",
    "ev_charger": "EV charger|Φορτιστής ηλεκτρικών οχημάτων|E-Ladestation|Borne de recharge|Punto de recarga|Зарядная станция|电动车充电桩|EV充電スタンド|شاحن سيارات كهربائية",
    "ev_available": "Available|Διαθέσιμος|Frei|Disponible|Disponible|Свободна|可用|空きあり|متاح",
    "ev_in_use": "In use|Σε χρήση|Belegt|Occupée|En uso|Занята|使用中|使用中|قيد الاستخدام",
    "ev_out_of_order": "Out of order|Εκτός λειτουργίας|Außer Betrieb|Hors service|Fuera de servicio|Не работает|故障|故障中|معطل",
    "ev_unknown": "Status unknown|Άγνωστη κατάσταση|Status unbekannt|Statut inconnu|Estado desconocido|Статус неизвестен|状态未知|状態不明|الحالة غير معروفة",
    "step_free": "Step-free access|Πρόσβαση χωρίς σκαλοπάτια|Stufenloser Zugang|Accès de plain-pied|Acceso sin escalones|Безбарьерный доступ|无障碍通道|段差なし|دخول بدون درج",
    # crowds (WiFi footfall)
    "quiet": "Quiet|Ήσυχα|Ruhig|Calme|Tranquilo|Спокойно|人少|空いている|هادئ",
    "usual": "As usual|Όπως συνήθως|Wie üblich|Comme d'habitude|Como de costumbre|Как обычно|正常|通常どおり|كالمعتاد",
    "busy": "Busy|Πολύς κόσμος|Belebt|Animé|Concurrido|Многолюдно|人多|混雑|مزدحم",
    # live crowds (the app's own users)
    "crowd_low": "Few people|Λίγος κόσμος|Wenig los|Peu de monde|Poca gente|Мало людей|人少|人が少ない|عدد قليل من الناس",
    "crowd_medium": "Some people|Αρκετός κόσμος|Mäßig besucht|Assez de monde|Algo de gente|Довольно людно|人较多|やや混雑|عدد متوسط من الناس",
    "crowd_high": "Crowded|Συνωστισμός|Sehr voll|Bondé|Muy concurrido|Очень людно|拥挤|大変混雑|مزدحم جدًا",
    # heat (NWS heat-index levels)
    "none": "Normal|Κανονική|Normal|Normale|Normal|Нормально|正常|通常|طبيعي",
    "caution": "Caution|Προσοχή|Vorsicht|Prudence|Precaución|Осторожно|注意|注意|حذر",
    "extreme_caution": "Extreme caution|Αυξημένη προσοχή|Erhöhte Vorsicht|Prudence extrême|Precaución extrema|Повышенная осторожность|高度注意|厳重注意|حذر شديد",
    "danger": "Danger|Κίνδυνος|Gefahr|Danger|Peligro|Опасно|危险|危険|خطر",
    "extreme_danger": "Extreme danger|Μεγάλος κίνδυνος|Extreme Gefahr|Danger extrême|Peligro extremo|Крайне опасно|极度危险|極めて危険|خطر شديد",
    # events
    "Music": "Music|Μουσική|Musik|Musique|Música|Музыка|音乐|音楽|موسيقى",
    "Sports": "Sports|Αθλητισμός|Sport|Sport|Deportes|Спорт|体育|スポーツ|رياضة",
    "Arts & Theatre": "Arts & Theatre|Τέχνες & Θέατρο|Kunst & Theater|Arts & Théâtre|Artes y teatro|Искусство и театр|艺术与戏剧|芸術・演劇|الفنون والمسرح",
    "Film": "Film|Κινηματογράφος|Film|Cinéma|Cine|Кино|电影|映画|أفلام",
    "Miscellaneous": "Miscellaneous|Διάφορα|Sonstiges|Divers|Varios|Разное|其他|その他|متنوع",
    "onsale": "On sale|Σε διάθεση|Im Verkauf|En vente|A la venta|В продаже|售票中|販売中|متاح للبيع",
    "offsale": "Sales closed|Εκτός διάθεσης|Verkauf beendet|Vente terminée|Venta cerrada|Продажа закрыта|已停售|販売終了|البيع مغلق",
    "today": "Today|Σήμερα|Heute|Aujourd'hui|Hoy|Сегодня|今天|今日|اليوم",
    "weekend": "This weekend|Αυτό το Σαββατοκύριακο|Dieses Wochenende|Ce week-end|Este fin de semana|В эти выходные|本周末|今週末|عطلة نهاية الأسبوع هذه",
    "week": "Next 7 days|Επόμενες 7 ημέρες|Nächste 7 Tage|7 prochains jours|Próximos 7 días|Следующие 7 дней|未来7天|今後7日間|الأيام السبعة القادمة",
}
LABELS = {code: dict(zip(LANGS, row.split("|"))) for code, row in _TABLE.items()}
assert all(len(v) == len(LANGS) for v in LABELS.values()), "every label needs all 9 languages"


def labels(lang):
    """{code: label} in `lang`; unknown language → English."""
    lang = lang if lang in LANGS else "en"
    return {"lang": lang, "dir": "rtl" if lang in RTL else "ltr", "labels": {c: v[lang] for c, v in LABELS.items()}}
