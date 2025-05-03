import time
import threading
import math as mt

session_duration = 10
ts = 0.001  # Tempo de amostragem definido pelo usuário
cycles = int(mt.floor(session_duration / ts)) + 1

def loop_amostragem(ts, cycles):
    start_time = time.perf_counter()

    for k in range(cycles):
        expected_time = start_time + k * ts
        now = time.perf_counter()
        
        # Aqui entra o que você quiser fazer em cada ciclo
        print(f"Iteração {k} - Tempo real: {now - start_time:.3f}s")

        # Calcula quanto tempo falta até o próximo tempo ideal
        sleep_time = expected_time + ts - time.perf_counter()
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(f"Atraso detectado na iteração {k}: {-sleep_time:.4f}s")

    total_time = time.perf_counter() - start_time
    print(f"Tempo total: {total_time:.4f}s | Δ médio: {total_time / cycles:.4f}s")

# Criando e iniciando uma thread dedicada para a amostragem
amostragem_thread = threading.Thread(target=loop_amostragem, args=(ts, cycles))
amostragem_thread.start()
amostragem_thread.join()
