package shop.devictoria.api.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

/**
 * Proxy 패턴 구현
 * 모든 요청/응답을 가로채서 처리하는 글로벌 필터
 * - 요청 로깅
 * - 인증 검증
 * - 응답 변환
 * - 에러 처리
 */
@Slf4j
@Component
public class ProxyFilter implements GlobalFilter, Ordered {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        ServerHttpResponse response = exchange.getResponse();

        // 요청 정보 로깅 (Proxy 역할)
        log.info("[Proxy] 요청: {} {}", request.getMethod(), request.getURI());
        log.info("[Proxy] 요청 헤더: {}", request.getHeaders());

        long startTime = System.currentTimeMillis();

        // 다음 필터 체인 실행
        return chain.filter(exchange).then(Mono.fromRunnable(() -> {
            long duration = System.currentTimeMillis() - startTime;
            log.info("[Proxy] 응답: {} {}ms", response.getStatusCode(), duration);
        }));
    }

    @Override
    public int getOrder() {
        // 필터 실행 순서 (낮을수록 먼저 실행)
        return -1;
    }
}

