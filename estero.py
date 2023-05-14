'''
Marta ENnrich Garcia
'''

import struct

def leeWave(fitWave):
    '''
    Lectura del fichero fitWave
    '''
    with open(fitWave, "rb") as fpWave:
        capcelera = '<4sI4s'
        chunkID, chunkSize, formato = struct.unpack(capcelera, fpWave.read(struct.calcsize(capcelera)))
        if chunkID != b'RIFF' or formato != b'WAVE':
            raise Exception('El fichero no tiene formato wave')

        fmtCap = '<4sI2H2I2H'
        (subChunk1ID, subChunk1Size, audioFormat, numChannels,
         sampleRate, byteRate, blockAlign, bitsPerSample) = struct.unpack(fmtCap, fpWave.read(struct.calcsize(fmtCap)))

        fmtData = '<4sI'
        subChunk2ID, subChunk2Size = struct.unpack(fmtData, fpWave.read(struct.calcsize(fmtData)))
        data = fpWave.read(subChunk2Size)

        bytesPerSample = bitsPerSample // 8
        fmtSample = 'h' if bytesPerSample == 2 else 'h'  # Use 'h' for both 16-bit and 32-bit samples

        if numChannels == 1:
            numSamples = subChunk2Size // bytesPerSample
            fmtSen = '<' + str(numSamples) + fmtSample
            senyal = [struct.unpack(fmtSen, data)]

        elif numChannels == 2:
            numSamples = subChunk2Size // (bytesPerSample * 2)
            fmtSen = '<' + str(numSamples * 2) + fmtSample
            senyal = struct.unpack(fmtSen, data)
            senyal = [senyal[::2], senyal[1::2]]

    return senyal, sampleRate

def writeWave(fileWave, signal, sampleRate):
    '''
    Escritura del fichero 
    '''
    with open(fileWave, 'wb') as fpWave:
        chunkSize = 44 + 2 * len(signal[0]) + 2 * (len(signal[1]) if len(signal) > 1 else 0)
        fpWave.write(struct.pack('<4sI4s', b'RIFF', chunkSize, b'WAVE'))

        fpWave.write(struct.pack('<4sI2H2I2H', b'fmt ', 16, 1, len(signal), sampleRate, 16 // 8 * sampleRate * len(signal), len(signal) * 16 // 8, 16))

        numMuestras = len(signal[0]) + (len(signal[1]) if len(signal) > 1 else 0)
        fpWave.write(struct.pack('<4sI', b'data', 2 * numMuestras))

        fmtSen = '<' + str(numMuestras) + 'h'

        if len(signal) == 1:
            fpWave.write(struct.pack(fmtSen, *signal[0]))

        elif len(signal) == 2:
            sen = [None] * (len(signal[0]) + len(signal[1]))
            sen[::2] = signal[0]
            sen[1::2] = signal[1]
            fpWave.write(struct.pack(fmtSen, *sen))

## 1: De estereo a mono
def estereo2mono(ficEste, ficMono, canal=2):
    '''
    La función lee el fichero ficEste, que debe contener una señal estéreo, y escribe el fichero ficMono,
    con una señal monofónica. El tipo concreto de señal que se almacenará en ficMono depende del argumento
    canal:
    - canal=0: Se almacena el canal izquierdo L.
    - canal=1: Se almacena el canal derecho R.
    - canal=2: Se almacena la semisuma (L+R)/2. Es la opción por defecto.
    - canal=3: Se almacena la semidiferencia (L-R)/2.
    '''
    signal, sampleRate = leeWave(ficEste)
    
    if canal == 0:
        writeWave(ficMono, [signal[0]], sampleRate)
    elif canal == 1:
        writeWave(ficMono, [signal[1]], sampleRate)
    elif canal == 2:
        semisuma = [(v1 + v2) // 2 for v1, v2 in zip(signal[0], signal[1])]
        writeWave(ficMono, [semisuma], sampleRate)
    elif canal == 3:
        semidiferencia = [(v1 - v2) // 2 for v1, v2 in zip(signal[0], signal[1])]
        writeWave(ficMono, [semidiferencia], sampleRate)


## 2: De mono a estereo
def mono2estereo(ficIzq, ficDer, ficEste):
        
    '''
    Lee los ficheros ficIzq y ficDer, que contienen las señales monofónicas correspondientes a los canales
    izquierdo y derecho, respectivamente, y construye con ellas una señal estéreo que almacena en el fichero
    ficEste.
    '''

    signalIzq, sampleRate = leeWave(ficIzq)
    signalDer, sampleRate = leeWave(ficDer)
    writeWave(ficEste, [*signalIzq, *signalDer], sampleRate)


## 3: Codificador estereo
def codEstereo(ficEste, ficCod):
    '''
    Lee el fichero \python{ficEste}, que contiene una señal estéreo codificada con PCM lineal de 16 bits, y
    construye con ellas una señal codificada con 32 bits que permita su reproducción tanto por sistemas
    monofónicos como por sistemas estéreo preparados para ello.
    '''
    signal, sampleRate = leeWave(ficEste)
    
    with open(ficCod, 'wb') as fpWave:
        chunkSize = 44 + 32 // 8 * len(signal[0]) + 32 // 8 * (len(signal[1]) if len(signal) > 1 else 0)
        fmtRiff = '<4sI4s'
        fpWave.write(struct.pack(fmtRiff, b'RIFF', chunkSize, b'WAVE'))
        
        fmtCap = '<4sI2H2I2H'
        fpWave.write(struct.pack(fmtCap, b'fmt ', 16, 1, 1, sampleRate, 32 // 8 * sampleRate * 1, 1 * 32 // 8, 32)) #1:audioformat fmlineal
        
        fmtData = '<4sI'
        numMuestras = len(signal[0]) + (len(signal[1]) if len(signal) > 1 else 0)
        fpWave.write(struct.pack(fmtData, b'data', 32 // 8 * numMuestras))
        
        fmtSen = '<' + str(numMuestras) + 'h'
        
        semisuma = [(v1 + v2) // 2 for v1, v2 in zip(signal[0], signal[1])]
        semidiferencia = [(v1 - v2) // 2 for v1, v2 in zip(signal[0], signal[1])]
        
        sen = [None] * (len(semisuma) + len(semidiferencia))
        sen[::2] = semisuma
        sen[1::2] = semidiferencia
        
        fpWave.write(struct.pack(fmtSen, *sen))


## 4: Descodificador estereo
def decEstereo(ficCod, ficEste):
    '''
    Lee el fichero \python{ficCod} con una señal monofónica de 32 bits en la que los 16 bits más significativos
    contienen la semisuma de los dos canales de una señal estéreo y los 16 bits menos significativos la
    semidiferencia, y escribe el fichero \python{ficEste} con los dos canales por separado en el formato de los
    ficheros WAVE estéreo.
    '''
    signal, sampleRate = leeWave(ficCod)
    
    with open(ficEste, 'wb') as fpWave:
        chunkSize = 44 + 2 * len(signal[0]) + 2 * (len(signal[1]) if len(signal) > 1 else 0)
        fmtRiff = '<4sI4s'
        fpWave.write(struct.pack(fmtRiff, b'RIFF', chunkSize, b'WAVE'))
        
        fmtCap = '<4sI2H2I2H'
        fpWave.write(struct.pack(fmtCap, b'fmt ', 16, 1, 2, sampleRate, 16 // 8 * sampleRate * 2, 2 * 16 // 8, 16)) #1:audioformat fmlineal
        
        fmtData = '<4sI'
        numMuestras = len(signal[0]) + (len(signal[1]) if len(signal) > 1 else 0)
        fpWave.write(struct.pack(fmtData, b'data', 2 * numMuestras))
                       
        fmtSen = '<' + str(numMuestras) + 'h'
        
        semisuma = signal[0][::2]
        semidiferencia = signal[0][1::2]
        
        sen = [None] * (len(semisuma) + len(semidiferencia))
        sen[::2] = [v1 + v2 for v1, v2 in zip(semisuma, semidiferencia)]
        sen[1::2] = [v1 - v2 for v1, v2 in zip(semisuma, semidiferencia)]
        
        fpWave.write(struct.pack(fmtSen, *sen))


# Comprobación de las funciones
signal, sampleRate = leeWave('wav/komm.wav')
writeWave("copia.wav", signal, sampleRate)
estereo2mono("wav/komm.wav", "izquierdo.wav", 0)
estereo2mono("wav/komm.wav", "derecho.wav", 1)
estereo2mono("wav/komm.wav", "semisuma.wav", 2)
estereo2mono("wav/komm.wav", "semidiferencia.wav", 3)
mono2estereo("izquierdo.wav", "derecho.wav", "Conjunto.wav")
codEstereo('wav/komm.wav', 'Codificado.wav')
decEstereo('Codificado.wav', 'DesCodificado.wav') 