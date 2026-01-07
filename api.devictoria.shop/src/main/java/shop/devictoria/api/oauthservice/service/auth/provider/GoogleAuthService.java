package shop.devictoria.api.service.auth.provider;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.client.WebClient;
import shop.devictoria.api.config.GoogleProperties;
import shop.devictoria.api.dto.auth.provider.GoogleTokenResponse;
import shop.devictoria.api.dto.auth.provider.GoogleUserInfo;

import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class GoogleAuthService {
    
    private final GoogleProperties googleProperties;
    private final WebClient.Builder webClientBuilder;
    private final RedisTemplate<String, String> redisTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    /**
     * 구글 인증 코드로 토큰 요청
     */
    public GoogleTokenResponse getGoogleToken(String authorizationCode) {
        System.out.println("[GoogleAuthService] 구글 토큰 요청 시작");
        System.out.println("[GoogleAuthService] 인증 코드: " + authorizationCode);
        System.out.println("[GoogleAuthService] Client ID: " + googleProperties.getClientId());
        System.out.println("[GoogleAuthService] Redirect URI: " + googleProperties.getRedirectUri());
        System.out.println("[GoogleAuthService] Token URI: " + googleProperties.getTokenUri());
        
        MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
        formData.add("grant_type", "authorization_code");
        formData.add("client_id", googleProperties.getClientId());
        formData.add("client_secret", googleProperties.getClientSecret());
        formData.add("redirect_uri", googleProperties.getRedirectUri());
        formData.add("code", authorizationCode);
        
        try {
            WebClient webClient = webClientBuilder.build();
            
            System.out.println("[GoogleAuthService] 구글 API에 토큰 요청 전송 중...");
            GoogleTokenResponse response = webClient.post()
                    .uri(googleProperties.getTokenUri())
                    .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                    .bodyValue(formData)
                    .retrieve()
                    .bodyToMono(GoogleTokenResponse.class)
                    .block();
            
            System.out.println("[GoogleAuthService] 구글 토큰 요청 성공!");
            System.out.println("[GoogleAuthService] 받은 Access Token: " + (response.getAccessToken() != null ? response.getAccessToken().substring(0, Math.min(20, response.getAccessToken().length())) + "..." : "null"));
            return response;
            
        } catch (Exception e) {
            System.out.println("[GoogleAuthService] 구글 토큰 요청 실패: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("구글 토큰 요청 실패", e);
        }
    }
    
    /**
     * 구글 액세스 토큰으로 사용자 정보 조회
     */
    public GoogleUserInfo getGoogleUserInfo(String accessToken) {
        System.out.println("[GoogleAuthService] 구글 사용자 정보 조회 시작");
        System.out.println("[GoogleAuthService] 사용할 Access Token: " + (accessToken != null ? accessToken.substring(0, Math.min(20, accessToken.length())) + "..." : "null"));
        System.out.println("[GoogleAuthService] User Info URI: " + googleProperties.getUserInfoUri());
        
        try {
            WebClient webClient = webClientBuilder.build();
            
            System.out.println("[GoogleAuthService] 구글 API에 사용자 정보 요청 전송 중...");
            GoogleUserInfo userInfo = webClient.get()
                    .uri(googleProperties.getUserInfoUri())
                    .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
                    .retrieve()
                    .bodyToMono(GoogleUserInfo.class)
                    .block();
            
            System.out.println("[GoogleAuthService] 구글 사용자 정보 조회 성공!");
            System.out.println("[GoogleAuthService] 사용자 ID: " + userInfo.getId());
            System.out.println("[GoogleAuthService] 이메일: " + userInfo.getEmail());
            System.out.println("[GoogleAuthService] 이름: " + userInfo.getName());
            return userInfo;
            
        } catch (Exception e) {
            System.out.println("[GoogleAuthService] 구글 사용자 정보 조회 실패: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("구글 사용자 정보 조회 실패", e);
        }
    }
    
    /**
     * 인증 코드로 구글 로그인 처리 (토큰 요청 + 사용자 정보 조회)
     */
    public GoogleUserInfo loginWithAuthorizationCode(String authorizationCode) {
        System.out.println("[GoogleAuthService] 인증 코드로 로그인 처리 시작");
        // 1. 인증 코드로 토큰 요청
        GoogleTokenResponse tokenResponse = getGoogleToken(authorizationCode);
        
        // 2. 토큰으로 사용자 정보 조회
        GoogleUserInfo userInfo = getGoogleUserInfo(tokenResponse.getAccessToken());
        
        // 3. 구글 토큰을 Redis에 저장
        saveGoogleTokenToRedis(userInfo.getId(), tokenResponse);
        
        return userInfo;
    }
    
    /**
     * 구글 토큰을 Redis에 저장
     */
    private void saveGoogleTokenToRedis(String userId, GoogleTokenResponse tokenResponse) {
        try {
            String key = "google:token:" + userId;
            String tokenJson = objectMapper.writeValueAsString(tokenResponse);
            
            // 구글 액세스 토큰 만료 시간 설정 (초 단위)
            long expiration = tokenResponse.getExpiresIn() != null ? 
                tokenResponse.getExpiresIn() : 3600; // 기본 1시간
            
            redisTemplate.opsForValue().set(key, tokenJson, expiration, TimeUnit.SECONDS);
            
            System.out.println("========================================");
            System.out.println("[GoogleAuthService] ✅ 구글 토큰을 Redis에 저장했습니다");
            System.out.println("[GoogleAuthService] Redis Key: " + key);
            System.out.println("[GoogleAuthService] 만료 시간: " + expiration + "초");
            System.out.println("[GoogleAuthService] 저장된 구글 Access Token: " + 
                (tokenResponse.getAccessToken() != null ? tokenResponse.getAccessToken().substring(0, Math.min(20, tokenResponse.getAccessToken().length())) + "..." : "null"));
            System.out.println("[GoogleAuthService] 저장된 구글 Refresh Token: " + 
                (tokenResponse.getRefreshToken() != null ? tokenResponse.getRefreshToken().substring(0, Math.min(20, tokenResponse.getRefreshToken().length())) + "..." : "null"));
            System.out.println("(이 토큰은 Redis에만 저장되고, 프론트엔드로는 반환되지 않습니다)");
            System.out.println("========================================");
        } catch (JsonProcessingException e) {
            System.out.println("[GoogleAuthService] Redis 저장 실패: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.out.println("[GoogleAuthService] Redis 저장 중 오류 발생: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * 액세스 토큰으로 구글 로그인 처리 (사용자 정보 조회만)
     */
    public GoogleUserInfo loginWithAccessToken(String accessToken) {
        System.out.println("[GoogleAuthService] 액세스 토큰으로 로그인 처리 시작");
        return getGoogleUserInfo(accessToken);
    }
}

