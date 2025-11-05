/**
 * ToolCallMessage Component
 *
 * Displays AI tool calls with collapsible arguments and results.
 */

import { Component } from '../base/Component.js';
import { div } from '../../utils/dom.js';

export interface ToolCallMessageProps {
  toolName: string;
  arguments: Record<string, unknown>;
  result?: unknown;
  timestamp: string;
}

/**
 * Tool call message component
 */
export class ToolCallMessage extends Component<ToolCallMessageProps> {
  private argumentsExpanded: boolean = false;
  private resultExpanded: boolean = false;

  constructor(props: ToolCallMessageProps) {
    super(props);
  }

  protected render(): HTMLElement {
    const { toolName, timestamp } = this.props;

    const message = div({ class: 'tool-call-message' });

    // Icon/badge
    const badge = div({ class: 'tool-call-message__badge' }, '🛠️');

    // Header
    const header = div({ class: 'tool-call-message__header' });

    const title = div({ class: 'tool-call-message__tool-name' }, toolName);

    const time = div({ class: 'tool-call-message__timestamp' }, this.formatTimestamp(timestamp));

    header.appendChild(badge);
    header.appendChild(title);
    header.appendChild(time);

    // Arguments section
    const argumentsSection = this.createArgumentsSection();

    // Result section (if available)
    let resultSection: HTMLElement | null = null;
    if (this.props.result !== undefined) {
      resultSection = this.createResultSection();
    }

    // Assemble message
    message.appendChild(header);
    message.appendChild(argumentsSection);
    if (resultSection) {
      message.appendChild(resultSection);
    }

    return message;
  }

  private createArgumentsSection(): HTMLElement {
    const section = div({ class: 'tool-call-message__section' });

    const sectionHeader = div({
      class: 'tool-call-message__section-header',
      onclick: () => this.toggleArguments(),
    });

    const arrow = div(
      { class: 'tool-call-message__arrow' },
      this.argumentsExpanded ? '▼' : '▶'
    );

    const label = div({ class: 'tool-call-message__section-label' }, 'Arguments');

    sectionHeader.appendChild(arrow);
    sectionHeader.appendChild(label);

    const content = div({ class: 'tool-call-message__section-content' });
    content.style.display = this.argumentsExpanded ? 'block' : 'none';

    const codeBlock = document.createElement('pre');
    codeBlock.className = 'tool-call-message__code-block';

    const code = document.createElement('code');
    code.textContent = JSON.stringify(this.props.arguments, null, 2);
    codeBlock.appendChild(code);

    content.appendChild(codeBlock);

    section.appendChild(sectionHeader);
    section.appendChild(content);

    return section;
  }

  private createResultSection(): HTMLElement {
    const section = div({ class: 'tool-call-message__section' });

    const sectionHeader = div({
      class: 'tool-call-message__section-header',
      onclick: () => this.toggleResult(),
    });

    const arrow = div(
      { class: 'tool-call-message__arrow' },
      this.resultExpanded ? '▼' : '▶'
    );

    const label = div({ class: 'tool-call-message__section-label' }, 'Result');

    sectionHeader.appendChild(arrow);
    sectionHeader.appendChild(label);

    const content = div({ class: 'tool-call-message__section-content' });
    content.style.display = this.resultExpanded ? 'block' : 'none';

    const codeBlock = document.createElement('pre');
    codeBlock.className = 'tool-call-message__code-block';

    const code = document.createElement('code');
    code.textContent = JSON.stringify(this.props.result, null, 2);
    codeBlock.appendChild(code);

    content.appendChild(codeBlock);

    section.appendChild(sectionHeader);
    section.appendChild(content);

    return section;
  }

  private toggleArguments(): void {
    this.argumentsExpanded = !this.argumentsExpanded;

    if (this.element) {
      const arrow = this.element.querySelector(
        '.tool-call-message__section:first-of-type .tool-call-message__arrow'
      );
      const content = this.element.querySelector(
        '.tool-call-message__section:first-of-type .tool-call-message__section-content'
      );

      if (arrow) {
        arrow.textContent = this.argumentsExpanded ? '▼' : '▶';
      }
      if (content) {
        (content as HTMLElement).style.display = this.argumentsExpanded ? 'block' : 'none';
      }
    }
  }

  private toggleResult(): void {
    this.resultExpanded = !this.resultExpanded;

    if (this.element) {
      const sections = this.element.querySelectorAll('.tool-call-message__section');
      if (sections.length > 1) {
        const resultSection = sections[1];
        if (!resultSection) return;

        const arrow = resultSection.querySelector('.tool-call-message__arrow');
        const content = resultSection.querySelector('.tool-call-message__section-content');

        if (arrow) {
          arrow.textContent = this.resultExpanded ? '▼' : '▶';
        }
        if (content) {
          (content as HTMLElement).style.display = this.resultExpanded ? 'block' : 'none';
        }
      }
    }
  }

  private formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString();
    } catch {
      return timestamp;
    }
  }
}
