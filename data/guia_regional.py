ESPECIES_DETALLADAS = [
    {
        "nombre": "Pavón (Tucunaré)",
        "tipo": "Depredador diurno",
        "habitat": "Bocas de caños, lagunas, palizadas y bordes de playas con poca corriente.",
        "carnada_senuelo": "Señuelos de superficie (poppers, hélices), minnows, jigs y sardina viva.",
        "equipo": "Multifilamento 20-30 lb + líder de fluorocarbono 30-40 lb.",
        "consejo": "Ataca con fuerza al amanecer (05:30-08:00) y al caer la tarde; trabaja el señuelo con pausas cortas.",
    },
    {
        "nombre": "Payara",
        "tipo": "Depredador de corriente",
        "habitat": "Raudales fuertes, chorros oxigenados y caídas detrás de piedras sumergidas.",
        "carnada_senuelo": "Minnows de paleta larga, cucharas metálicas pesadas y carnada viva a la deriva.",
        "equipo": "Multifilamento 30-40 lb + guaya de acero obligatoria de 40-50 lb.",
        "consejo": "Mantén la punta de la caña alta al clavar para evitar que suelte el señuelo en los saltos.",
    },
    {
        "nombre": "Morocoto / Morocoto Piedrero",
        "tipo": "Omnívoro / Frugívoro de fuerza",
        "habitat": "Lajas de piedra con corriente, raudales moderados y zonas de rebalse.",
        "carnada_senuelo": "Masa fermentada de maíz o plátano, frutas de monte y trozos de pescado fresco.",
        "equipo": "Anzuelo corto reforzado #1/0 a #3/0 + líder fluorocarbono 40-50 lb.",
        "consejo": "Tiene mandíbula muy dura; usa anzuelos gruesos que no se abran y ceba el punto antes de lanzar.",
    },
    {
        "nombre": "Bagre (Rayado, Cajaro, Dorado, Valentón)",
        "tipo": "Depredador de fondo / Nocturno",
        "habitat": "Pozos profundos, canales principales y salidas de caños durante la noche.",
        "carnada_senuelo": "Filete sangrante de palometa o bocachico, lisa entera o carnada viva de fondo.",
        "equipo": "Plomada corrediza de 2 a 6 oz + líder de 50-80 lb + anzuelo #4/0 a #7/0.",
        "consejo": "Deja que tome línea unos segundos antes de clavar firme; los mejores piques ocurren tras anochecer.",
    },
    {
        "nombre": "Picúa (Bicuda)",
        "tipo": "Depredador veloz de superficie",
        "habitat": "Corrientes rápidas, puntas de islas y playas con paso de cardúmenes.",
        "carnada_senuelo": "Señuelos alargados tipo lápiz o minnow recogidos a alta velocidad y sardina viva.",
        "equipo": "Multifilamento 20-30 lb + guaya fina de acero o fluorocarbono de 40-50 lb.",
        "consejo": "No detengas el señuelo; prefiere recogidas rápidas y erráticas cerca de la superficie.",
    },
    {
        "nombre": "Palometa",
        "tipo": "Omnívoro de cardumen",
        "habitat": "Remansos, bordes de corriente suave y zonas previamente cebadas.",
        "carnada_senuelo": "Masa de trigo con queso, maíz dulce, trocitos de carne o vísceras.",
        "equipo": "Anzuelo pequeño reforzado #4 a #1 + línea de 15-20 lb.",
        "consejo": "Tiene boca pequeña y cortante; usa bolitas de masa pequeñas que tapen justo la punta del anzuelo.",
    },
    {
        "nombre": "Curvina de Río",
        "tipo": "Depredador de fondo arenoso",
        "habitat": "Playas hondas, canales de arena/fango y salidas de remansos.",
        "carnada_senuelo": "Vinilos/grubs de 2 pulgadas (verde fluorescente o blanco) con jighead 1/8-3/8 oz, o camarón.",
        "equipo": "Anzuelo #1/#2 + líder fluorocarbono 15-20 lb.",
        "consejo": "Recoge el vinilo dando pequeños saltos pegados al fondo; suele andar en grupos.",
    },
    {
        "nombre": "Cubanita (Cabeza de Manteco)",
        "tipo": "Herbívoro / Omnívoro de orilla",
        "habitat": "Piedras sumergidas, empalizadas y remansos tranquilos.",
        "carnada_senuelo": "Masa elástica de harina de trigo con queso y vainilla, lombriz o maíz cocido.",
        "equipo": "Anzuelo fino #6 a #2 + plomada ligera de 1/4 a 1/2 oz.",
        "consejo": "Pica con toques muy sutiles; mantén la línea tensa para sentir la picada al instante.",
    },
    {
        "nombre": "Cachama",
        "tipo": "Frugívoro / Omnívoro de rebalse",
        "habitat": "Caños lentos, lagunas conectadas al río y zonas con árboles frutales en la orilla.",
        "carnada_senuelo": "Masa fermentada de plátano maduro, semillas, frutas y maíz remojado.",
        "equipo": "Anzuelo reforzado #2/0 a #4/0 + líder 40-60 lb.",
        "consejo": "En época de río subiendo busca las orillas inundadas donde caen semillas y frutos.",
    },
    {
        "nombre": "Caribe / Piraña",
        "tipo": "Carnívoro de cardumen",
        "habitat": "Remansos, lagunas y bordes de caños.",
        "carnada_senuelo": "Trocitos de carne roja o pescado fresco (también sirve como carnada viva para bagre).",
        "equipo": "Empate corto de guaya fina de acero (corta el nylon fácilmente).",
        "consejo": "Si cortan tus vinilos o carnadas constantemente, muévete unos metros hacia zona con más corriente.",
    },
    {
        "nombre": "Sardina / Bocachico / Agujón",
        "tipo": "Peces de carnada (Forraje)",
        "habitat": "Orillas poco profundas, playas de arena y entradas de caños.",
        "carnada_senuelo": "Bolitas diminutas de masa de trigo o atarraya para recolectar carnada viva.",
        "equipo": "Anzuelo #10 a #8 y línea fina de 8-12 lb.",
        "consejo": "Mantenerlos vivos en un balde con recambio constante de agua garantiza éxito con payara y pavón.",
    },
]

GUIA_CARNADAS = [
    {
        "nombre": "1. Masa Fermentada de Maíz (Morocoto, Cachama y Palometa)",
        "tipo": "Masa artesanal",
        "ingredientes": "1 kg de maíz pilado (o harina de maíz), 150 g de papelón rallado, 15 g de levadura y agua tibia.",
        "preparacion": [
            "1. Cocina el maíz hasta que ablande o mezcla la harina con agua tibia y el papelón disuelto.",
            "2. Añade la levadura y amasa hasta lograr una textura firme que no se deshaga fácil.",
            "3. Guarda en un envase plástico con tapa floja (para que salgan los gases) de 24 a 48 horas a la sombra.",
            "4. En el río, si queda muy blanda, ajústala agregando un poco de harina seca.",
        ],
    },
    {
        "nombre": "2. Masa Elástica de Trigo y Queso (Cubanita, Palometa y Bocachico)",
        "tipo": "Masa rápida sin fermentar",
        "ingredientes": "500 g de harina de trigo todo uso, 150 g de queso blanco rallado salado, 1 cucharada de vainilla.",
        "preparacion": [
            "1. Mezcla en seco la harina de trigo con el queso bien rallado.",
            "2. Agrega la vainilla y ve sumando agua poco a poco mientras amasas con fuerza durante 8 minutos.",
            "3. El punto exacto es cuando la masa estira como chicle y no se pega a los dedos, resistiendo corrientes fuertes.",
        ],
    },
    {
        "nombre": "3. Masa de Plátano Maduro (Morocoto Piedrero y Cachama)",
        "tipo": "Masa dulce natural",
        "ingredientes": "3 plátanos bien maduros (concha negra), 400 g de harina de maíz o trigo y 2 cucharadas de miel/papelón.",
        "preparacion": [
            "1. Tritura los plátanos maduros hasta obtener un puré sin grumos.",
            "2. Incorpora la harina poco a poco y amasa hasta conseguir una bola compacta y aromática.",
            "3. Ideal para encarnar bolitas del tamaño de una metras sobre anzuelos #1/0 o #2/0.",
        ],
    },
    {
        "nombre": "4. Carnada Viva (Sardina, Bocachico pequeño, Caribe)",
        "tipo": "Carnada natural viva",
        "ingredientes": "Peces de 8 a 15 cm capturados en la misma zona del río.",
        "preparacion": [
            "1. Para pesca en corriente o raudal (Payara/Picúa): pasa el anzuelo de abajo hacia arriba por ambos labios para que nade natural contra el agua.",
            "2. Para pesca con boya o remanso (Pavón): engancha suavemente por el lomo debajo de la aleta dorsal sin tocar la espina.",
            "3. Cambia el agua del balde cada 20 minutos para mantenerla oxigenada.",
        ],
    },
    {
        "nombre": "5. Postas y Filetes Sangrantes (Bagre Rayado, Cajaro y Dorado)",
        "tipo": "Carnada de fondo",
        "ingredientes": "Palometa, bocachico o lisa fresca.",
        "preparacion": [
            "1. Corta tiras o postas gruesas dejando siempre la piel intacta para que el anzuelo tenga buen agarre.",
            "2. Haz 2 o 3 cortes superficiales en la pulpa para que libere sangre y aceite en la corriente.",
            "3. Pasa el anzuelo dos veces por la piel (cosido) para evitar que la corriente o peces pequeños la arranquen.",
        ],
    },
]

METODOS_CEBADEROS = [
    {
        "nombre": "Saco Calado en Cabecera de Corriente",
        "ideal_para": "Morocoto, Palometa, Cubanita y Bagre",
        "como_hacerlo": [
            "1. Usa un saco de malla fina (tipo saco cebollero) y mete adentro piedras pesadas junto con maíz remojado, restos de masa y vísceras de pescado.",
            "2. Amarra la boca del saco con un mecate resistente y fíjalo a una piedra grande o tronco sumergido unos 5 a 10 metros río arriba de donde vas a lanzar.",
            "3. La corriente lavará lentamente el contenido creando un túnel de olor que atrae y mantiene el cardumen en tu zona.",
        ],
    },
    {
        "nombre": "Bolas de Masa con Arcilla o Arena de Río",
        "ideal_para": "Pozos profundos y corrientes medias",
        "como_hacerlo": [
            "1. Mezcla masa fermentada de maíz con tierra arcillosa o arena húmeda de la orilla (proporción 50/50) para darle peso.",
            "2. Forma 5 o 6 bolas del tamaño de una naranja y lánzalas unos metros río arriba del punto donde caerán tus plomadas.",
            "3. Al llegar al fondo se deshacen poco a poco sin ser arrastradas lejos por la corriente.",
        ],
    },
    {
        "nombre": "Botella o Tubo Cebador Perforado",
        "ideal_para": "Pesca embarcada (bongo) o desde lajas altas",
        "como_hacerlo": [
            "1. Toma una botella plástica de 1.5 L o 2 L y hazle unos 25 agujeros con un clavo caliente.",
            "2. Rellena con piedras, masa blanda fermentada y trozos de pescado machacado.",
            "3. Bájala atada con nylon grueso hasta que toque el fondo justo debajo del bote o frente a la piedra.",
        ],
    },
    {
        "nombre": "Cebado Sonoro de Superficie (Granos y Frutas)",
        "ideal_para": "Morocoto Piedrero y Palometa en rebalse",
        "como_hacerlo": [
            "1. Lleva un envase con granos de maíz cocido o trozos pequeños de plátano/guayaba.",
            "2. Arroja un puñado pequeño cada 3 a 4 minutos golpeando ligeramente el agua para imitar frutos cayendo de los árboles.",
            "3. Apenas veas lomos o remolinos subiendo a comer, lanza tu línea con un solo grano o bolita de masa sin plomo (a línea libre).",
        ],
    },
]
