import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QLabel, QPushButton, QScrollArea)
from PyQt6.QtCore import Qt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import io
from PyQt6.QtGui import QPixmap, QImage
import numpy as np

class LatexEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A Simple LaTeX Formula Viewer")
        self.setGeometry(100, 100, 1200, 600)
        
        # Add unsupported commands list at the beginning of the class
        self.unsupported_commands = {
            'align': 'align',
            'array': 'array',
            'mathbf': 'mathbf',
            'eqnarray': 'eqnarray',
            'gather': 'gather',
            'cases': 'cases',
            'matrix': 'matrix',
            'bmatrix': 'bmatrix',
            'pmatrix': 'pmatrix',
            'vmatrix': 'vmatrix',
            'split': 'split',
            'substack': 'substack',
            'displaystyle': 'displaystyle',
            'boldsymbol': 'boldsymbol',
        }
        
        # Add alternative suggestions
        self.command_alternatives = {
            'mathbf': 'can be replaced by \\text{}',
            'array': 'can be replaced by multiple \\frac{}{}',
            'cases': 'can be replaced by multiple lines of \\frac{}{}',
            'matrix': 'can be replaced by \\frac{}{}',
        }
        
        # create main window widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # create horizontal layout
        layout = QHBoxLayout()
        main_widget.setLayout(layout)
        
        # Left panel - LaTeX input
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Create input area
        self.input_area = QTextEdit()
        self.input_area.setPlaceholderText("Enter LaTeX formula here...")
        left_layout.addWidget(QLabel("LaTeX Input:"))
        left_layout.addWidget(self.input_area)
        
        # Add common symbols buttons
        symbols_layout = QVBoxLayout()
        symbols = [
            ("Basic Operations", ["+", "-", "\\times", "\\div", "=", "\\neq", "\\approx"]),
            ("Subscripts and Superscripts", ["^", "_", "\\sqrt{}", "\\frac{}{}"]),
            ("Greek Letters", ["\\alpha", "\\beta", "\\gamma", "\\theta", "\\pi", "\\sigma", "\\omega"]),
            ("Set Symbols", ["\\in", "\\notin", "\\subset", "\\subseteq", "\\cup", "\\cap"]),
            ("Arrows", ["\\rightarrow", "\\leftarrow", "\\Rightarrow", "\\Leftarrow"]),
            ("Sum and Integral", ["\\sum", "\\prod", "\\int", "\\oint", "\\lim"]),
            ("Parentheses", ["()", "[]", "\\{\\}", "\\langle\\rangle"]),
        ]
        
        for category, symbol_list in symbols:
            category_label = QLabel(category)
            symbols_layout.addWidget(category_label)
            
            buttons_layout = QHBoxLayout()
            for symbol in symbol_list:
                btn = QPushButton(symbol)
                btn.clicked.connect(lambda checked, s=symbol: self.insert_symbol(s))
                buttons_layout.addWidget(btn)
            
            symbols_layout.addLayout(buttons_layout)
        
        left_layout.addLayout(symbols_layout)
        
        # Add preview button
        preview_btn = QPushButton("Preview Formula")
        preview_btn.clicked.connect(self.update_preview)
        left_layout.addWidget(preview_btn)
        
        # Right panel - Preview area
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        right_layout.addWidget(QLabel("Preview:"))
        
        # Create preview area
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        
        # Put preview area in scroll area
        preview_container = QWidget()
        preview_container_layout = QVBoxLayout()
        preview_container_layout.addWidget(self.preview_label)
        preview_container_layout.addStretch()  # Add stretchable space
        preview_container.setLayout(preview_container_layout)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(preview_container)
        scroll_area.setWidgetResizable(True)
        right_layout.addWidget(scroll_area)

        # Add panels to main layout
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        
        self.update_preview()

    def insert_symbol(self, symbol):
        """Insert LaTeX symbol at cursor position"""
        cursor = self.input_area.textCursor()
        cursor.insertText(symbol)
    
    def check_latex_compatibility(self, latex):
        """Check LaTeX code compatibility"""
        warnings = []
        for cmd, description in self.unsupported_commands.items():
            if f'\\{cmd}' in latex or f'\\begin{{{cmd}}}' in latex:
                warning = f'Unsupported {description} (\\{cmd})'
                if cmd in self.command_alternatives:
                    warning += f'\nSuggestion: {self.command_alternatives[cmd]}'
                warnings.append(warning)
        return warnings

    def preprocess_latex(self, latex):
        """Preprocess LaTeX code, remove or replace unsupported commands"""
        # Remove all environments
        environments = ['align', 'cases', 'pmatrix', 'bmatrix', 'vmatrix', 'matrix', 'array', 'eqnarray', 'gather', 'split']
        for env in environments:
            # Remove \begin{env} and \end{env}
            latex = latex.replace(f'\\begin{{{env}}}', '')
            latex = latex.replace(f'\\end{{{env}}}', '')
        
        # Replace commands
        replacements = {
            '\\mathbf{': '\\text{',  # Replace bold with plain text
            '\\boldsymbol{': '\\text{',  # Replace bold symbols with plain text
            '\\displaystyle': '',  # Remove display style command
            '\\substack{': '',  # Remove subscript stacking
            '\\\\': ',',  # Replace newline with comma
            '&': ' ',  # Remove alignment symbol
        }
        
        for old, new in replacements.items():
            latex = latex.replace(old, new)
        
        return latex

    def update_preview(self):
        """Update formula preview"""
        try:
            # Get LaTeX code
            latex = self.input_area.toPlainText()
            
            # Check compatibility and display warnings
            warnings = self.check_latex_compatibility(latex)
            if warnings:
                warning_msg = "Warning:\n" + "\n".join(warnings)
                warning_msg += "\n\nTrying to remove unsupported commands and render..."
                self.preview_label.setText(warning_msg)
            
            # Preprocess LaTeX code
            latex = self.preprocess_latex(latex)
            
            # Get preview area size
            preview_width = self.preview_label.width()
            preview_height = self.preview_label.height()
            
            # Use higher DPI for better clarity
            base_dpi = 300
            scale_factor = 2  # Scale factor for better clarity
            
            # Calculate figure size, considering high DPI
            fig_width = preview_width * scale_factor / base_dpi
            fig_height = preview_height * scale_factor / base_dpi
            
            # Create figure, using higher DPI
            fig = Figure(figsize=(fig_width, fig_height), dpi=base_dpi)
            ax = fig.add_subplot(111)
            
            # Set background transparent
            fig.patch.set_alpha(0.0)
            ax.patch.set_alpha(0.0)
            
            # Hide axes
            ax.axis('off')
            
            # Render LaTeX formula, adjusting font size based on scale
            fontsize = 12 * scale_factor
            ax.text(0.5, 0.5, f"${latex}$",
                   horizontalalignment='center',
                   verticalalignment='center',
                   fontsize=fontsize,
                   transform=ax.transAxes)
            
            # Convert figure to image
            buf = io.BytesIO()
            fig.savefig(buf, format='png', 
                       dpi=base_dpi,
                       bbox_inches='tight',
                       pad_inches=0.1,
                       transparent=True)
            buf.seek(0)
            
            # Display image in preview area
            image = QImage.fromData(buf.getvalue())
            
            # Scale image based on preview area size
            scaled_pixmap = QPixmap.fromImage(image).scaled(
                preview_width,
                preview_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.preview_label.setPixmap(scaled_pixmap)
            
            plt.close(fig)
            
        except Exception as e:
            self.preview_label.setText(f"Rendering error: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LatexEditor()
    window.show()
    sys.exit(app.exec())
