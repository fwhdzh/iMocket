package imocket.ImplDiffIdentifier;

import com.github.javaparser.JavaParser;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.VariableDeclarator;
import com.github.javaparser.ast.expr.AnnotationExpr;
import com.github.javaparser.ast.expr.AssignExpr;
import com.github.javaparser.utils.SourceRoot;

import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public class ImplDiffIdentifier {

    public static void main(String[] args) throws IOException {
        if (args.length != 3) {
            System.out.println("Usage: java -jar ImplDiffIdentifier.jar <path/to/project1> <path/to/project2> <path/to/output_file>");
            System.exit(1);
        }
        compareProjects(args[0], args[1], args[2]);
    }

    private static void compareProjects(String path1, String path2, String outputPath) throws IOException {
        SourceRoot sourceRoot1 = new SourceRoot(Paths.get(path1));
        SourceRoot sourceRoot2 = new SourceRoot(Paths.get(path2));
        
        List<CompilationUnit> units1 = sourceRoot1.tryToParse("");
        List<CompilationUnit> units2 = sourceRoot2.tryToParse("");

        List<String> differences = new ArrayList<>();

        for (int i = 0; i < units1.size(); i++) {
            CompilationUnit unit1 = units1.get(i);
            CompilationUnit unit2 = units2.get(i);
            
            unit1.findAll(ClassOrInterfaceDeclaration.class).forEach(class1 -> {
                String className = class1.getNameAsString();
                unit2.findAll(ClassOrInterfaceDeclaration.class).stream()
                    .filter(class2 -> class2.getNameAsString().equals(className))
                    .findFirst()
                    .ifPresent(class2 -> compareClasses(class1, class2, differences));
            });
        }

        try (FileWriter writer = new FileWriter(outputPath)) {
            for (String diff : differences) {
                writer.write(diff + "\n");
            }
        }
    }

    private static void compareClasses(ClassOrInterfaceDeclaration class1, ClassOrInterfaceDeclaration class2, List<String> differences) {
        class1.getMethods().forEach(method1 -> {
            String methodName = method1.getNameAsString();
            class2.getMethods().stream()
                .filter(method2 -> method2.getNameAsString().equals(methodName))
                .findFirst()
                .ifPresent(method2 -> compareMethods(method1, method2, differences));
        });
    }

    private static void compareMethods(MethodDeclaration method1, MethodDeclaration method2, List<String> differences) {
        boolean method1HasAction = method1.isAnnotationPresent("Action");
        boolean method2HasAction = method2.isAnnotationPresent("Action");

        if (method1HasAction && method2HasAction) {
            StringBuilder result = new StringBuilder("Action method modified: " + method1.getNameAsString() + ", Changes: ");
            method1.findAll(VariableDeclarator.class).forEach(var -> {
                if (var.isAnnotationPresent("Variable")) {
                    method1.findAll(AssignExpr.class).forEach(assign -> {
                        if (assign.getTarget().toString().equals(var.getNameAsString())) {
                            result.append(assign.toString() + "; ");
                        }
                    });
                }
            });
            differences.add(result.toString());
        }
    }
}