package projects.sampleProject;

@Repository
public class UserRepository {

    private List<User> users = new ArrayList<>(
            List.of(
                    new User(1L, "Samir Zade", "samir@gmail.com", "Pune"),
                    new User(2L, "Rahul Sharma", "rahul@gmail.com", "Mumbai"),
                    new User(3L, "Priya Patel", "priya@gmail.com", "Ahmedabad"),
                    new User(4L, "Anjali Singh", "anjali@gmail.com", "Delhi"),
                    new User(5L, "Rohit Verma", "rohit@gmail.com", "Bangalore")
            )
    );

    public List<User> findAll() {
        return users;
    }

    public User findById(Long id) {
        return users.stream()
                .filter(user -> user.getId().equals(id))
                .findFirst()
                .orElse(null);
    }
}
