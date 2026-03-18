package docman.controller;

import docman.dto.CreateDirectoryRequest;
import docman.entity.ProjectDocument;
import docman.service.DirectoryService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/directory")
@RequiredArgsConstructor
public class DirectoryController {

    private final DirectoryService directoryService;

    @PostMapping(value = "/create", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<ProjectDocument> createDirectory(@RequestBody CreateDirectoryRequest request) {
        return ResponseEntity.ok(directoryService.createDirectory(request));
    }

    @GetMapping("/{projectId}")
    public ResponseEntity<ProjectDocument> getProject(@PathVariable String projectId) {
        return ResponseEntity.ok(directoryService.getProject(projectId));
    }
}