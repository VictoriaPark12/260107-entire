package shop.devictoria.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * API Gateway 애플리케이션
 * 
 * Spring Cloud Gateway (WebFlux 기반)와 Spring MVC를 함께 사용합니다.
 * - Gateway 라우팅은 WebFlux로 처리
 * - OAuth 컨트롤러는 MVC로 처리 (RedirectView 사용 가능)
 * 
 * 주의: Spring Boot가 자동으로 WebFlux와 MVC를 공존시킵니다.
 * Gateway는 WebFlux 기반으로 동작하고, MVC 컨트롤러는 별도로 처리됩니다.
 */
@SpringBootApplication
public class ApiApplication {

	public static void main(String[] args) {
		SpringApplication.run(ApiApplication.class, args);
	}

}
