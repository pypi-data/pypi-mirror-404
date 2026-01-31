#!/usr/bin/env node
/**
 * TypeScript AST parser using TypeScript compiler API
 * Outputs JSON representation of AST for Python consumption
 */

const ts = require('typescript');
const fs = require('fs');
const path = require('path');

function parseTypeScriptFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');

    const sourceFile = ts.createSourceFile(
        path.basename(filePath),
        content,
        ts.ScriptTarget.Latest,
        true
    );

    const entities = {
        classes: [],
        functions: [],
        imports: []
    };

    function visit(node) {
        // Extract classes and interfaces
        if (ts.isClassDeclaration(node) || ts.isInterfaceDeclaration(node)) {
            entities.classes.push(extractClass(node, sourceFile));
        }

        // Extract top-level functions (not methods)
        if (ts.isFunctionDeclaration(node)) {
            entities.functions.push(extractFunction(node, sourceFile, false));
        }

        // Extract arrow functions assigned to variables
        if (ts.isVariableStatement(node)) {
            node.declarationList.declarations.forEach(decl => {
                if (decl.initializer && ts.isArrowFunction(decl.initializer)) {
                    const funcData = extractArrowFunction(decl, sourceFile);
                    if (funcData) {
                        entities.functions.push(funcData);
                    }
                }
            });
        }

        // Extract imports
        if (ts.isImportDeclaration(node)) {
            entities.imports.push(extractImport(node, sourceFile));
        }

        ts.forEachChild(node, visit);
    }

    visit(sourceFile);
    return entities;
}

function extractClass(node, sourceFile) {
    const pos = sourceFile.getLineAndCharacterOfPosition(node.getStart());
    const end = sourceFile.getLineAndCharacterOfPosition(node.getEnd());

    const methods = [];
    const properties = [];
    const baseClasses = [];

    // Extract heritage (extends/implements)
    if (node.heritageClauses) {
        node.heritageClauses.forEach(clause => {
            clause.types.forEach(type => {
                baseClasses.push(type.expression.getText(sourceFile));
            });
        });
    }

    // Extract members
    const methodEntities = [];
    if (node.members) {
        node.members.forEach(member => {
            if (ts.isMethodDeclaration(member) || ts.isMethodSignature(member)) {
                const methodName = member.name ? member.name.getText(sourceFile) : 'anonymous';
                methods.push(methodName);
                // Also extract method as a function entity with calls
                methodEntities.push(extractFunction(member, sourceFile, true));
            } else if (ts.isPropertyDeclaration(member) || ts.isPropertySignature(member)) {
                const propName = member.name ? member.name.getText(sourceFile) : 'anonymous';
                properties.push(propName);
            }
        });
    }

    // Extract JSDoc comment
    const docstring = extractDocstring(node, sourceFile);

    return {
        name: node.name ? node.name.text : 'anonymous',
        line_start: pos.line + 1,
        line_end: end.line + 1,
        methods: methods,
        properties: properties,
        base_classes: baseClasses,
        is_abstract: node.modifiers?.some(m => m.kind === ts.SyntaxKind.AbstractKeyword) || false,
        decorators: extractDecorators(node),
        docstring: docstring,
        method_entities: methodEntities  // Full method data with calls
    };
}

function extractFunction(node, sourceFile, isMethod = false) {
    const pos = sourceFile.getLineAndCharacterOfPosition(node.getStart());
    const end = sourceFile.getLineAndCharacterOfPosition(node.getEnd());

    const parameters = node.parameters.map(p => p.name.getText(sourceFile));

    let returnType = null;
    if (node.type) {
        returnType = node.type.getText(sourceFile);
    }

    const isAsync = node.modifiers?.some(m => m.kind === ts.SyntaxKind.AsyncKeyword) || false;
    const isStatic = node.modifiers?.some(m => m.kind === ts.SyntaxKind.StaticKeyword) || false;

    // Extract JSDoc comment
    const docstring = extractDocstring(node, sourceFile);

    // Extract function calls
    const calls = extractCalls(node.body, sourceFile);

    return {
        name: node.name ? node.name.text : 'anonymous',
        line_start: pos.line + 1,
        line_end: end.line + 1,
        parameters: parameters,
        return_type: returnType,
        is_async: isAsync,
        is_method: isMethod,
        is_static: isStatic,
        decorators: extractDecorators(node),
        docstring: docstring,
        calls: calls
    };
}

function extractArrowFunction(variableDecl, sourceFile) {
    const arrowFunc = variableDecl.initializer;
    const pos = sourceFile.getLineAndCharacterOfPosition(arrowFunc.getStart());
    const end = sourceFile.getLineAndCharacterOfPosition(arrowFunc.getEnd());

    const name = variableDecl.name.getText(sourceFile);
    const parameters = arrowFunc.parameters.map(p => p.name.getText(sourceFile));

    let returnType = null;
    if (arrowFunc.type) {
        returnType = arrowFunc.type.getText(sourceFile);
    }

    // Extract function calls from arrow function body
    const calls = extractCalls(arrowFunc.body, sourceFile);

    return {
        name: name,
        line_start: pos.line + 1,
        line_end: end.line + 1,
        parameters: parameters,
        return_type: returnType,
        is_async: false,  // Arrow functions don't have async modifier at declaration level
        is_method: false,
        is_static: false,
        decorators: [],
        docstring: null,
        calls: calls
    };
}

/**
 * Extract all function calls from a node (function body)
 * @param {ts.Node} node - The AST node to search for calls
 * @param {ts.SourceFile} sourceFile - The source file
 * @returns {string[]} - Array of called function names
 */
function extractCalls(node, sourceFile) {
    if (!node) return [];

    const calls = new Set();

    function visitForCalls(n) {
        if (ts.isCallExpression(n)) {
            const callName = getCallName(n.expression, sourceFile);
            if (callName) {
                calls.add(callName);
            }
        }
        ts.forEachChild(n, visitForCalls);
    }

    visitForCalls(node);
    return Array.from(calls);
}

/**
 * Get the name of a called function from its expression
 * @param {ts.Expression} expr - The call expression
 * @param {ts.SourceFile} sourceFile - The source file
 * @returns {string|null} - The function name or null
 */
function getCallName(expr, sourceFile) {
    // Direct call: foo()
    if (ts.isIdentifier(expr)) {
        return expr.text;
    }

    // Method call: obj.foo() or obj.bar.foo()
    if (ts.isPropertyAccessExpression(expr)) {
        const parts = [];
        let current = expr;

        while (ts.isPropertyAccessExpression(current)) {
            parts.unshift(current.name.text);
            current = current.expression;
        }

        if (ts.isIdentifier(current)) {
            parts.unshift(current.text);
        }

        return parts.join('.');
    }

    // Element access: obj['foo']() - less common but handle it
    if (ts.isElementAccessExpression(expr)) {
        const objName = getCallName(expr.expression, sourceFile);
        if (expr.argumentExpression && ts.isStringLiteral(expr.argumentExpression)) {
            return objName ? `${objName}.${expr.argumentExpression.text}` : expr.argumentExpression.text;
        }
        return objName;
    }

    // Chained call: foo()() - get the inner function
    if (ts.isCallExpression(expr)) {
        return getCallName(expr.expression, sourceFile);
    }

    return null;
}

function extractImport(node, sourceFile) {
    const moduleSpecifier = node.moduleSpecifier.text;
    const line = sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1;

    let importedNames = [];
    let alias = null;

    if (node.importClause) {
        // Default import: import Foo from 'module'
        if (node.importClause.name) {
            importedNames.push(node.importClause.name.text);
        }

        // Named imports: import { A, B } from 'module'
        if (node.importClause.namedBindings) {
            if (ts.isNamedImports(node.importClause.namedBindings)) {
                node.importClause.namedBindings.elements.forEach(element => {
                    importedNames.push(element.name.text);
                });
            }
            // Namespace import: import * as Foo from 'module'
            else if (ts.isNamespaceImport(node.importClause.namedBindings)) {
                alias = node.importClause.namedBindings.name.text;
            }
        }
    }

    return {
        module: moduleSpecifier,
        line_number: line,
        imported_names: importedNames,
        alias: alias
    };
}

function extractDecorators(node) {
    if (!node.decorators) return [];

    return node.decorators.map(decorator => {
        return decorator.expression.getText();
    });
}

function extractDocstring(node, sourceFile) {
    const jsDocComments = ts.getJSDocCommentsAndTags(node);
    if (jsDocComments && jsDocComments.length > 0) {
        return jsDocComments[0].comment || null;
    }
    return null;
}

// Main execution
const filePath = process.argv[2];
if (!filePath) {
    console.error('Usage: node ts_ast_parser.js <file.ts>');
    process.exit(1);
}

try {
    const result = parseTypeScriptFile(filePath);
    console.log(JSON.stringify(result, null, 2));
} catch (error) {
    console.error('Error parsing TypeScript:', error.message);
    process.exit(1);
}
