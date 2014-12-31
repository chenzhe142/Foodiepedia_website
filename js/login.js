App.NavbarController = Ember.ArrayController.extend({
  isAuthenticated: false,
  login: function() {
    this.set('isAuthenticated', true);
  },
  logout: function() {
    this.set('isAuthenticated', false);
  }
});