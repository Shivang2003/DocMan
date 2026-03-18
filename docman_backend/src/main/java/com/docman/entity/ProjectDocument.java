package docman.entity;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.util.ArrayList;
import java.util.List;

@Data
@Document(collection = "projects")
public class ProjectDocument {

    @Id
    private String id;

    private String projectName;
    private String createdAt;

    private List<Directory> directories = new ArrayList<>();
}