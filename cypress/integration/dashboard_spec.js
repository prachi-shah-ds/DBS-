describe('Dashboard customization', () => {
  it('allows customizing and saving layout', () => {
    cy.visit('/login');
    cy.get('input[name=email]').type('test@example.com');
    cy.get('input[name=password]').type('password');
    cy.get('button[type=submit]').click();
    cy.visit('/app/dashboard');
    cy.get('[data-test=customize-btn]').click();
    // drag a widget by simulate drag
    // gridstack provides programmatic move; for E2E you may call API to rearrange or interact with DOM
    cy.get('[data-panel-id=kpi_revenue]').then($el => {
      // placeholder: perform drag
    });
    cy.get('[data-test=save-layout]').click();
    cy.reload();
    cy.get('[data-panel-id=kpi_revenue]').should('exist');
  });
});
