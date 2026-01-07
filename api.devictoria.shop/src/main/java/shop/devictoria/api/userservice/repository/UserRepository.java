package shop.devictoria.api.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import shop.devictoria.api.domain.SocialProvider;
import shop.devictoria.api.domain.User;

import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    
    Optional<User> findByEmail(String email);
    
    Optional<User> findByProviderAndProviderId(SocialProvider provider, String providerId);
    
    boolean existsByEmail(String email);
    
    boolean existsByProviderAndProviderId(SocialProvider provider, String providerId);
}

