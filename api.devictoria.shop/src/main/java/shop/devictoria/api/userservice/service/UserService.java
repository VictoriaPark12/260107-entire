package shop.devictoria.api.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import shop.devictoria.api.domain.SocialProvider;
import shop.devictoria.api.domain.User;
import shop.devictoria.api.dto.SocialLoginRequest;
import shop.devictoria.api.dto.UserResponse;
import shop.devictoria.api.exception.UserNotFoundException;
import shop.devictoria.api.repository.UserRepository;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;

    /**
     * 소셜 로그인 처리 - 신규 사용자 생성 또는 기존 사용자 업데이트
     */
    @Transactional
    public UserResponse processSocialLogin(SocialLoginRequest request) {
        log.info("소셜 로그인 처리 시작 - Provider: {}, Email: {}", request.getProvider(), request.getEmail());

        User user = userRepository
                .findByProviderAndProviderId(request.getProvider(), request.getProviderId())
                .map(existingUser -> {
                    log.info("기존 사용자 발견 - ID: {}", existingUser.getId());
                    existingUser.updateProfile(request.getName(), request.getProfileImage());
                    existingUser.updateLastLogin();
                    return existingUser;
                })
                .orElseGet(() -> {
                    log.info("신규 사용자 생성");
                    User newUser = User.builder()
                            .email(request.getEmail())
                            .name(request.getName())
                            .provider(request.getProvider())
                            .providerId(request.getProviderId())
                            .profileImage(request.getProfileImage())
                            .phoneNumber(request.getPhoneNumber())
                            .isActive(true)
                            .build();
                    newUser.updateLastLogin();
                    return userRepository.save(newUser);
                });

        log.info("소셜 로그인 처리 완료 - User ID: {}", user.getId());
        return UserResponse.from(user);
    }

    /**
     * 사용자 ID로 조회
     */
    public UserResponse getUserById(Long id) {
        log.info("사용자 조회 - ID: {}", id);
        User user = userRepository.findById(id)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. ID: " + id));
        return UserResponse.from(user);
    }

    /**
     * 이메일로 사용자 조회
     */
    public UserResponse getUserByEmail(String email) {
        log.info("사용자 조회 - Email: {}", email);
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. Email: " + email));
        return UserResponse.from(user);
    }

    /**
     * 소셜 제공자와 제공자 ID로 사용자 조회
     */
    public UserResponse getUserByProviderAndProviderId(SocialProvider provider, String providerId) {
        log.info("사용자 조회 - Provider: {}, ProviderId: {}", provider, providerId);
        User user = userRepository.findByProviderAndProviderId(provider, providerId)
                .orElseThrow(() -> new UserNotFoundException(
                        String.format("사용자를 찾을 수 없습니다. Provider: %s, ProviderId: %s", provider, providerId)));
        return UserResponse.from(user);
    }

    /**
     * 모든 사용자 조회
     */
    public List<UserResponse> getAllUsers() {
        log.info("전체 사용자 조회");
        return userRepository.findAll().stream()
                .map(UserResponse::from)
                .collect(Collectors.toList());
    }

    /**
     * 사용자 비활성화
     */
    @Transactional
    public void deactivateUser(Long id) {
        log.info("사용자 비활성화 - ID: {}", id);
        User user = userRepository.findById(id)
                .orElseThrow(() -> new UserNotFoundException("사용자를 찾을 수 없습니다. ID: " + id));
        user.setIsActive(false);
    }

    /**
     * 사용자 삭제
     */
    @Transactional
    public void deleteUser(Long id) {
        log.info("사용자 삭제 - ID: {}", id);
        if (!userRepository.existsById(id)) {
            throw new UserNotFoundException("사용자를 찾을 수 없습니다. ID: " + id);
        }
        userRepository.deleteById(id);
    }
}

