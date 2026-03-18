package docman.service;

import docman.dto.CreateDirectoryRequest;
import docman.entity.Directory;
import docman.entity.ProjectDocument;
import docman.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class DirectoryService {

    private final ProjectRepository projectRepository;

    public ProjectDocument createDirectory(CreateDirectoryRequest req) {

        // 1- Fetch existing project OR create new one
        ProjectDocument project = projectRepository.findById(req.getProjectId())
                .orElseGet(() -> {
                    ProjectDocument newProject = new ProjectDocument();
                    newProject.setId(req.getProjectId());
                    newProject.setProjectName(req.getProjectName());
                    newProject.setCreatedAt(LocalDateTime.now().toString());
                    return newProject;
                });

        // 2- Build Directory Object
        Directory dir = new Directory();
        dir.setDirectoryId(UUID.randomUUID().toString());
        dir.setDirectoryName(req.getDirectoryName());
        dir.setIndexName(req.getIndexName());
        dir.setType(req.getType());
        dir.setCreatedAt(LocalDateTime.now().toString());

        // 3- Add directory to project
        project.getDirectories().add(dir);

        // 4- Save and return project
        return projectRepository.save(project);
    }

    public ProjectDocument getProject(String projectId) {
        return projectRepository.findById(projectId)
                .orElseThrow(() -> new RuntimeException("Project not found"));
    }
}
