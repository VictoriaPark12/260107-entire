package shop.devictoria.api.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import shop.devictoria.api.domain.SocialProvider;
import shop.devictoria.api.dto.ApiResponse;
import shop.devictoria.api.dto.SocialLoginRequest;
import shop.devictoria.api.dto.UserResponse;
import shop.devictoria.api.service.UserService;

import java.util.List;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Slf4j
public class UserController {

    private final UserService userService;

    /**
     * 소셜 로그인 엔드포인트
     * POST /api/v1/users/social-login
     */
    @PostMapping("/social-login")
    public ResponseEntity<ApiResponse<UserResponse>> socialLogin(
            @Valid @RequestBody SocialLoginRequest request) {
        log.info("소셜 로그인 요청 - Provider: {}, Email: {}", request.getProvider(), request.getEmail());
        UserResponse userResponse = userService.processSocialLogin(request);
        return ResponseEntity
                .status(HttpStatus.OK)
                .body(ApiResponse.success("소셜 로그인 성공", userResponse));
    }

    /**
     * 사용자 ID로 조회
     * GET /api/v1/users/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<UserResponse>> getUserById(@PathVariable Long id) {
        log.info("사용자 조회 요청 - ID: {}", id);
        UserResponse userResponse = userService.getUserById(id);
        return ResponseEntity.ok(ApiResponse.success(userResponse));
    }

    /**
     * 이메일로 사용자 조회
     * GET /api/v1/users/email/{email}
     */
    @GetMapping("/email/{email}")
    public ResponseEntity<ApiResponse<UserResponse>> getUserByEmail(@PathVariable String email) {
        log.info("사용자 조회 요청 - Email: {}", email);
        UserResponse userResponse = userService.getUserByEmail(email);
        return ResponseEntity.ok(ApiResponse.success(userResponse));
    }

    /**
     * 소셜 제공자와 제공자 ID로 사용자 조회
     * GET /api/v1/users/social/{provider}/{providerId}
     */
    @GetMapping("/social/{provider}/{providerId}")
    public ResponseEntity<ApiResponse<UserResponse>> getUserBySocial(
            @PathVariable SocialProvider provider,
            @PathVariable String providerId) {
        log.info("소셜 사용자 조회 요청 - Provider: {}, ProviderId: {}", provider, providerId);
        UserResponse userResponse = userService.getUserByProviderAndProviderId(provider, providerId);
        return ResponseEntity.ok(ApiResponse.success(userResponse));
    }

    /**
     * 모든 사용자 조회
     * GET /api/v1/users
     */
    @GetMapping
    public ResponseEntity<ApiResponse<List<UserResponse>>> getAllUsers() {
        log.info("전체 사용자 조회 요청");
        List<UserResponse> users = userService.getAllUsers();
        return ResponseEntity.ok(ApiResponse.success(users));
    }

    /**
     * 사용자 비활성화
     * PATCH /api/v1/users/{id}/deactivate
     */
    @PatchMapping("/{id}/deactivate")
    public ResponseEntity<ApiResponse<Void>> deactivateUser(@PathVariable Long id) {
        log.info("사용자 비활성화 요청 - ID: {}", id);
        userService.deactivateUser(id);
        return ResponseEntity.ok(ApiResponse.success("사용자가 비활성화되었습니다", null));
    }

    /**
     * 사용자 삭제
     * DELETE /api/v1/users/{id}
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteUser(@PathVariable Long id) {
        log.info("사용자 삭제 요청 - ID: {}", id);
        userService.deleteUser(id);
        return ResponseEntity.ok(ApiResponse.success("사용자가 삭제되었습니다", null));
    }

    /**
     * Health Check
     * GET /api/v1/users/health
     */
    @GetMapping("/health")
    public ResponseEntity<ApiResponse<String>> healthCheck() {
        return ResponseEntity.ok(ApiResponse.success("User Service is running"));
    }
}

