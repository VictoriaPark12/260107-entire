package shop.devictoria.api.facade;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.Map;

/**
 * Facade 패턴 구현
 * 여러 마이크로서비스를 조합하여 통합 API 제공
 * 클라이언트는 복잡한 서비스 구조를 알 필요 없이 단일 인터페이스로 접근
 */
@Slf4j
@RestController
@RequestMapping("/api/facade")
@RequiredArgsConstructor
public class AggregateFacadeController {

    private final WebClient.Builder webClientBuilder;

    /**
     * Facade 예시: 사용자 정보 + 타이타닉 승객 정보를 한 번에 조회
     * 여러 서비스를 조합하여 단일 응답 제공
     */
    @GetMapping("/dashboard")
    public Mono<ResponseEntity<Map<String, Object>>> getDashboard() {
        log.info("[Facade] 대시보드 통합 정보 요청");

        WebClient webClient = webClientBuilder.build();

        // 여러 서비스 호출을 조합
        Mono<Map<String, Object>> userInfo = webClient.get()
                .uri("http://userservice:8082/api/user/profile")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .onErrorReturn(new HashMap<>())
                .defaultIfEmpty(new HashMap<>());

        Mono<Map<String, Object>> titanicInfo = webClient.get()
                .uri("http://titanic-service:9006/passengers/top10")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .onErrorReturn(new HashMap<>())
                .defaultIfEmpty(new HashMap<>());

        // 두 서비스의 결과를 조합하여 단일 응답 생성
        return Mono.zip(userInfo, titanicInfo)
                .map(tuple -> {
                    Map<String, Object> response = new HashMap<>();
                    response.put("user", tuple.getT1());
                    response.put("titanic", tuple.getT2());
                    response.put("timestamp", System.currentTimeMillis());
                    return ResponseEntity.ok(response);
                })
                .onErrorResume(e -> {
                    log.error("[Facade] 대시보드 정보 조회 실패", e);
                    Map<String, Object> errorResponse = new HashMap<>();
                    errorResponse.put("error", "대시보드 정보를 불러올 수 없습니다");
                    return Mono.just(ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse));
                });
    }

    /**
     * Facade 예시: 헬스 체크 통합
     * 모든 서비스의 상태를 한 번에 확인
     */
    @GetMapping("/health")
    public Mono<ResponseEntity<Map<String, Object>>> getHealth() {
        log.info("[Facade] 통합 헬스 체크 요청");

        WebClient webClient = webClientBuilder.build();

        // 여러 서비스의 헬스 체크를 병렬로 실행
        Mono<Map<String, Object>> oauthHealth = webClient.get()
                .uri("http://oauth-service:8080/actuator/health")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .onErrorReturn(createErrorHealth("oauth-service"))
                .defaultIfEmpty(createErrorHealth("oauth-service"));

        Mono<Map<String, Object>> userHealth = webClient.get()
                .uri("http://userservice:8082/actuator/health")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .onErrorReturn(createErrorHealth("user-service"))
                .defaultIfEmpty(createErrorHealth("user-service"));

        Mono<Map<String, Object>> titanicHealth = webClient.get()
                .uri("http://titanic-service:9006/health")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .onErrorReturn(createErrorHealth("titanic-service"))
                .defaultIfEmpty(createErrorHealth("titanic-service"));

        // 모든 서비스 상태를 조합
        return Mono.zip(oauthHealth, userHealth, titanicHealth)
                .map(tuple -> {
                    Map<String, Object> response = new HashMap<>();
                    response.put("oauth-service", tuple.getT1());
                    response.put("user-service", tuple.getT2());
                    response.put("titanic-service", tuple.getT3());
                    response.put("gateway", Map.of("status", "UP"));
                    return ResponseEntity.ok(response);
                });
    }

    private Map<String, Object> createErrorHealth(String service) {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "DOWN");
        health.put("service", service);
        return health;
    }
}

